
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

import pyotp
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings
from src.backend.app.database.models.admin_mfa import (
    AdminMfaCredential,
    AdminMfaRecoveryCode,
)
from src.backend.app.database.models.oauth_identity import OAuthIdentity
from src.backend.app.database.models.user import User
from src.backend.app.services.admin_totp import (
    encrypt_totp_secret,
    generate_totp_secret,
)


def matching_step(secret: str, code: str) -> int | None:
    totp = pyotp.TOTP(secret)
    step = int(datetime.now(timezone.utc).timestamp()) // totp.interval

    for candidate in (step - 1, step, step + 1):
        if candidate >= 0 and hmac.compare_digest(
            totp.at(candidate * totp.interval), code
        ):
            return candidate

    return None


def main() -> None:
    if not settings.debug:
        raise SystemExit("Development mode is required.")

    engine = create_engine(settings.database_url)

    try:
        with Session(engine) as db:
            database = db.scalar(text("SELECT current_database()"))

            if database != "careerforge":
                raise SystemExit("Expected CareerForge development database.")

            email = input("Admin email: ").strip().lower()

            admin = db.scalar(
                select(User).where(
                    func.lower(func.btrim(User.email)) == email
                )
            )

            if admin is None or admin.role != "admin":
                raise SystemExit("Administrator account not found.")

            identity = db.scalar(
                select(OAuthIdentity).where(
                    OAuthIdentity.user_id == admin.id,
                    OAuthIdentity.provider == "google",
                )
            )

            if identity is None:
                raise SystemExit("A linked Google identity is required.")

            record = db.get(AdminMfaCredential, admin.id)

            if record is not None and record.enabled_at is not None:
                raise SystemExit("Authenticator is already enrolled.")

            secret = generate_totp_secret()

            print("\nAdd a time-based account to your authenticator:")
            print(f"Account: {admin.email}")
            print(f"Issuer: {settings.mfa_issuer}")
            print(f"Setup key: {secret}")
            print("Type: Time based (TOTP)\n")

            code = input("Enter the current six-digit code: ").strip()

            if len(code) != 6 or not code.isascii() or not code.isdecimal():
                raise SystemExit("Invalid code format.")

            step = matching_step(secret, code)

            if step is None:
                raise SystemExit("Code verification failed. Nothing saved.")

            confirmation = input("Type ENROLL to activate MFA: ")

            if confirmation != "ENROLL":
                raise SystemExit("Enrollment cancelled.")

            now = datetime.now(timezone.utc)

            if record is None:
                record = AdminMfaCredential(user_id=admin.id)
                db.add(record)

            record.totp_secret_encrypted = encrypt_totp_secret(secret)
            record.pending_secret_encrypted = None
            record.pending_expires_at = None
            record.enabled_at = now
            record.last_accepted_step = step
            record.failed_attempts = 0
            record.locked_until = None
            record.mfa_version = (record.mfa_version or 1) + 1

            recovery_codes = [
                secrets.token_hex(16) for _ in range(8)
            ]

            for recovery_code in recovery_codes:
                db.add(
                    AdminMfaRecoveryCode(
                        user_id=admin.id,
                        code_hash=hashlib.sha256(
                            recovery_code.encode("ascii")
                        ).hexdigest(),
                    )
                )

            db.commit()

            print("\nAuthenticator enrolled successfully.")
            print("\nSAVE THESE RECOVERY CODES:")
            for recovery_code in recovery_codes:
                print(recovery_code)

            print("\nThese codes will not be displayed again.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
