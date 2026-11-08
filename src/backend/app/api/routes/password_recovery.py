
import hashlib
import logging
import secrets
from collections import deque
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.backend.app.core.security import hash_password, verify_password
from src.backend.app.database.models.password_reset_token import PasswordResetToken
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from src.backend.app.services.email_service import (
    send_password_changed_email,
    send_password_reset_email,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

RESET_LIFETIME = timedelta(minutes=15)
REQUEST_COOLDOWN = timedelta(seconds=60)
GENERIC_MESSAGE = "If an eligible account exists, a reset link will be sent."

attempts: dict[str, deque[float]] = {}
attempt_lock = Lock()


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=40, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


def limit_requests(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = monotonic()

    with attempt_lock:
        for key in list(attempts):
            while attempts[key] and now - attempts[key][0] > 3600:
                attempts[key].popleft()
            if not attempts[key]:
                del attempts[key]

        history = attempts.setdefault(ip, deque())

        if len(history) >= 10:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            )

        history.append(now)


def deliver_email(sender, recipient: str, token: str | None = None) -> None:
    try:
        if token is None:
            sender(recipient)
        else:
            sender(recipient, token)
    except Exception:
        logger.exception("CareerForge password recovery email delivery failed.")


@router.post("/forgot-password", status_code=202)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    limit_requests(request)
    normalized_email = payload.email.strip().lower()
    now = datetime.now(timezone.utc)

    user = db.scalar(
        select(User)
        .where(func.lower(func.btrim(User.email)) == normalized_email)
        .with_for_update()
    )

    if (
        user is None
        or user.password_hash is None
        or user.email_verified_at is None
        or user.suspended_at is not None
    ):
        return {"message": GENERIC_MESSAGE}

    record = db.get(PasswordResetToken, user.id)

    if record is not None:
        if now - record.created_at < REQUEST_COOLDOWN:
            return {"message": GENERIC_MESSAGE}

    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()

    if record is None:
        record = PasswordResetToken(user_id=user.id)
        db.add(record)

    record.token_hash = digest
    record.created_at = now
    record.expires_at = now + RESET_LIFETIME

    recipient = user.email
    db.commit()

    background_tasks.add_task(
        deliver_email,
        send_password_reset_email,
        recipient,
        token,
    )

    return {"message": GENERIC_MESSAGE}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    limit_requests(request)
    digest = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    invalid = HTTPException(400, "Invalid or expired reset link.")

    user_id = db.scalar(
        select(PasswordResetToken.user_id)
        .where(PasswordResetToken.token_hash == digest)
    )

    if user_id is None:
        raise invalid

    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
    )

    if user is None:
        raise invalid

    record = db.scalar(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.token_hash == digest,
        )
        .with_for_update()
    )

    if (
        record is None
        or record.expires_at <= datetime.now(timezone.utc)
        or user.password_hash is None
        or user.email_verified_at is None
        or user.suspended_at is not None
    ):
        raise invalid

    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(
            400, "Your new password must be different from your old password."
        )

    user.password_hash = hash_password(payload.new_password)
    user.session_version += 1

    recipient = user.email
    db.delete(record)
    db.commit()

    response.delete_cookie("careerforge_session", path="/api")
    response.delete_cookie("csrf_token", path="/")
    response.headers["Cache-Control"] = "no-store"

    background_tasks.add_task(
        deliver_email,
        send_password_changed_email,
        recipient,
    )

    return {"message": "Password reset successful. Please sign in again."}
