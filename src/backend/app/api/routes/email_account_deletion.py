
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from src.backend.app.services.email_service import (
    EmailDeliveryError,
    send_account_deletion_email,
)

router = APIRouter(prefix="/account", tags=["Account"])
logger = logging.getLogger(__name__)


class ConfirmDeletion(BaseModel):
    token: str = Field(min_length=40, max_length=128)
    email: EmailStr
    confirmation: str


@router.get("/me/deletion-method")
def deletion_method(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(401, "Account not found.")

    return {
        "has_password": user.password_hash is not None,
        "email": user.email,
    }


@router.post("/me/deletion-request", status_code=202)
def request_deletion(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)

    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
    )

    if user is None:
        raise HTTPException(401, "Account not found.")

    if user.role == "admin":
        raise HTTPException(403, "Administrator deletion is restricted.")

    if user.password_hash is not None:
        raise HTTPException(
            400,
            "Use password confirmation for this account.",
        )

    previous = db.execute(
        text("""
            SELECT created_at
            FROM account_deletion_tokens
            WHERE user_id = :user_id
            FOR UPDATE
        """),
        {"user_id": user.id},
    ).scalar_one_or_none()

    if previous and previous > now - timedelta(seconds=60):
        raise HTTPException(
            429,
            "Please wait before requesting another deletion email.",
        )

    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode()).hexdigest()

    db.execute(
        text("""
            INSERT INTO account_deletion_tokens
                (user_id, token_hash, expires_at)
            VALUES
                (:user_id, :digest, :expires_at)
            ON CONFLICT (user_id)
            DO UPDATE SET
                token_hash = EXCLUDED.token_hash,
                expires_at = EXCLUDED.expires_at,
                created_at = NOW()
        """),
        {
            "user_id": user.id,
            "digest": digest,
            "expires_at": now + timedelta(minutes=10),
        },
    )

    recipient = user.email
    db.commit()

    try:
        send_account_deletion_email(recipient, token)
    except EmailDeliveryError as exc:
        db.execute(
            text("""
                DELETE FROM account_deletion_tokens
                WHERE token_hash = :digest
            """),
            {"digest": digest},
        )
        db.commit()
        logger.warning(
            "Deletion confirmation email failed for user %s",
            user_id,
        )
        raise HTTPException(
            502,
            "Could not send the deletion confirmation email.",
        ) from exc

    return {"message": "Deletion confirmation email sent."}


@router.post("/deletion/confirm")
def confirm_deletion(
    payload: ConfirmDeletion,
    response: Response,
    db: Session = Depends(get_db),
):
    if payload.confirmation != "DELETE":
        raise HTTPException(400, "Confirmation must be DELETE.")

    digest = hashlib.sha256(payload.token.encode()).hexdigest()

    user_id = db.execute(
        text("""
            SELECT user_id
            FROM account_deletion_tokens
            WHERE token_hash = :digest
        """),
        {"digest": digest},
    ).scalar_one_or_none()

    if user_id is None:
        raise HTTPException(400, "Invalid or expired deletion link.")

    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
    )

    if user is None:
        raise HTTPException(400, "Deletion request is no longer valid.")

    expiry = db.execute(
        text("""
            SELECT expires_at
            FROM account_deletion_tokens
            WHERE user_id = :user_id
              AND token_hash = :digest
            FOR UPDATE
        """),
        {"user_id": user.id, "digest": digest},
    ).scalar_one_or_none()

    if (
        expiry is None
        or expiry <= datetime.now(timezone.utc)
        or user.email.strip().lower() != payload.email.strip().lower()
        or user.password_hash is not None
        or user.role == "admin"
    ):
        raise HTTPException(400, "Invalid or expired deletion link.")

    try:
        db.execute(delete(User).where(User.id == user.id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.warning(
            "Account deletion blocked by related records for user %s",
            user_id,
        )
        raise HTTPException(
            409,
            "Account deletion is blocked by related records. "
            "No account data was deleted.",
        ) from exc

    response.delete_cookie("careerforge_session", path="/api")
    response.delete_cookie("csrf_token", path="/")

    logger.info("User account %s deleted after email confirmation.", user_id)
    return {"message": "Your CareerForge account has been deleted."}
