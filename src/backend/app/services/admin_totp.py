
import pyotp
from cryptography.fernet import Fernet, InvalidToken

from src.backend.app.core.config import settings


def _cipher() -> Fernet:
    key = settings.mfa_encryption_key

    if not key:
        raise RuntimeError("MFA_ENCRYPTION_KEY is not configured.")

    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise RuntimeError("Invalid MFA encryption key.") from exc


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def encrypt_totp_secret(secret: str) -> str:
    return _cipher().encrypt(
        secret.encode("ascii")
    ).decode("ascii")


def decrypt_totp_secret(encrypted_secret: str) -> str:
    try:
        return _cipher().decrypt(
            encrypted_secret.encode("ascii")
        ).decode("ascii")
    except (InvalidToken, UnicodeEncodeError) as exc:
        raise RuntimeError(
            "Unable to decrypt the authenticator secret."
        ) from exc


def get_totp_provisioning_uri(
    secret: str,
    email: str,
) -> str:
    return pyotp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.mfa_issuer,
    )
