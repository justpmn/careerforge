
import hmac
from datetime import datetime, timedelta, timezone

import pyotp
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.admin_mfa import AdminMfaCredential
from src.backend.app.services.admin_totp import decrypt_totp_secret


MAX_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


def verify_and_consume_admin_totp(
    db: Session,
    user_id: int,
    code: str,
) -> int:
    now = datetime.now(timezone.utc)

    record = db.scalar(
        select(AdminMfaCredential)
        .where(AdminMfaCredential.user_id == user_id)
        .with_for_update()
    )

    if (
        record is None
        or record.enabled_at is None
        or record.totp_secret_encrypted is None
    ):
        raise HTTPException(
            status_code=403,
            detail="Administrator MFA is not enrolled.",
        )

    if record.locked_until and record.locked_until > now:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
        )

    if record.locked_until and record.locked_until <= now:
        record.failed_attempts = 0
        record.locked_until = None

    secret = decrypt_totp_secret(record.totp_secret_encrypted)
    totp = pyotp.TOTP(secret)

    current_step = int(now.timestamp()) // totp.interval
    matched_step = None

    if len(code) == 6 and code.isascii() and code.isdecimal():
        for step in (
            current_step - 1,
            current_step,
            current_step + 1,
        ):
            if step < 0:
                continue

            expected = totp.at(step * totp.interval)

            if hmac.compare_digest(expected, code):
                matched_step = step
                break

    previous_step = record.last_accepted_step

    if (
        matched_step is None
        or (
            previous_step is not None
            and matched_step <= previous_step
        )
    ):
        record.failed_attempts += 1

        if record.failed_attempts >= MAX_ATTEMPTS:
            record.locked_until = now + LOCKOUT_DURATION

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid or already used authenticator code.",
        )

    record.last_accepted_step = matched_step
    record.failed_attempts = 0
    record.locked_until = None

    version = record.mfa_version
    db.commit()

    return version
