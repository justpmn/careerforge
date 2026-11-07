
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone


TOKEN_LIFETIME = timedelta(hours=24)
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")


def hash_verification_token(token: str) -> str:
    if not TOKEN_PATTERN.fullmatch(token):
        raise ValueError("Invalid verification token.")

    return hashlib.sha256(
        token.encode("ascii")
    ).hexdigest()


def generate_verification_token() -> tuple[str, str, datetime]:
    token = secrets.token_urlsafe(32)
    token_hash = hash_verification_token(token)
    expires_at = datetime.now(timezone.utc) + TOKEN_LIFETIME

    return token, token_hash, expires_at
