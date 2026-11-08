
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.backend.app.database.models.user import User
from src.backend.app.database.models.email_verification_token import EmailVerificationToken
from src.backend.app.database.session import get_db
from src.backend.app.services.email_verification_tokens import (
    generate_verification_token,
    hash_verification_token,
)
from src.backend.app.services.email_service import (
    EmailDeliveryError,
    send_verification_email,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

RESEND_COOLDOWN = timedelta(minutes=2)
RESEND_MESSAGE = (
    "If this account requires verification and is eligible, "
    "a new verification email will be sent."
)


class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=43, max_length=43)


class ResendVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class MessageResponse(BaseModel):
    message: str


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    try:
        token_hash = hash_verification_token(payload.token)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification link.",
        )

    now = datetime.now(timezone.utc)

    record = db.scalar(
        select(EmailVerificationToken)
        .where(EmailVerificationToken.token_hash == token_hash)
        .with_for_update()
    )

    if record is None or record.expires_at <= now:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification link.",
        )

    user = db.get(User, record.user_id)

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification link.",
        )

    try:
        user.email_verified_at = now
        db.delete(record)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return MessageResponse(
        message="Your email address has been verified."
    )


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    email = str(payload.email).strip().lower()
    now = datetime.now(timezone.utc)

    user = db.scalar(
        select(User)
        .where(func.lower(func.btrim(User.email)) == email)
        .with_for_update()
    )

    if (
        user is None
        or user.email_verified_at is not None
        or user.password_hash is None
    ):
        return MessageResponse(message=RESEND_MESSAGE)

    record = db.get(EmailVerificationToken, user.id)

    if (
        record is not None
        and record.created_at is not None
        and now - record.created_at < RESEND_COOLDOWN
    ):
        return MessageResponse(message=RESEND_MESSAGE)

    token, token_hash, expires_at = generate_verification_token()

    try:
        if record is None:
            db.add(
                EmailVerificationToken(
                    user_id=user.id,
                    token_hash=token_hash,
                    expires_at=expires_at,
                )
            )
        else:
            record.token_hash = token_hash
            record.created_at = now
            record.expires_at = expires_at

        db.commit()
    except Exception:
        db.rollback()
        raise

    try:
        send_verification_email(user.email, token)
    except EmailDeliveryError:
        logger.exception(
            "Verification email delivery failed for user %s.",
            user.id,
        )

    return MessageResponse(message=RESEND_MESSAGE)
