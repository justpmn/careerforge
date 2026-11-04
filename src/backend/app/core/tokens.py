
from datetime import datetime, timedelta, timezone
import secrets
import jwt
from jwt.exceptions import InvalidTokenError

from src.backend.app.core.config import settings


JWT_ALGORITHM = "HS256"
JWT_ISSUER = "careerforge"
JWT_AUDIENCE = "careerforge-api"


def get_jwt_secret() -> str:
    secret = settings.jwt_secret_key

    if not secret or len(secret.encode("utf-8")) < 32:
        raise RuntimeError(
            "A secure JWT_SECRET_KEY must be configured."
        )

    return secret


def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
    *,
    admin_mfa_version: int | None = None,
) -> str:
    if type(user_id) is not int or user_id <= 0:
        raise ValueError("Invalid user ID.")

    now = datetime.now(timezone.utc)

    lifetime = (
        expires_delta
        if expires_delta is not None
        else timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    )

    payload = {
        "sub": str(user_id),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "exp": now + lifetime,
        "token_type": "access",
    }
    if admin_mfa_version is not None:
        if type(admin_mfa_version) is not int or admin_mfa_version < 1:
            raise ValueError("Invalid MFA version.")

        payload["admin_mfa_version"] = admin_mfa_version

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={
                "require": [
                    "sub",
                    "iss",
                    "aud",
                    "iat",
                    "exp",
                    "token_type",
                ]
            },
        )

        if payload["token_type"] != "access":
            raise ValueError("Invalid token type.")

        subject = payload["sub"]

        if (
            not isinstance(subject, str)
            or not subject.isascii()
            or not subject.isdecimal()
        ):
            raise ValueError("Invalid token subject.")

        user_id = int(subject)

        if user_id <= 0 or str(user_id) != subject:
            raise ValueError("Invalid token subject.")

        return user_id

    except InvalidTokenError as exc:
        raise ValueError(
            "Invalid or expired access token."
        ) from exc


def create_admin_mfa_challenge_token(user_id: int) -> str:
    if type(user_id) is not int or user_id <= 0:
        raise ValueError("Invalid user ID.")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "jti": secrets.token_urlsafe(16),
        "token_type": "admin_mfa_challenge",
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def decode_admin_mfa_challenge_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={
                "require": [
                    "sub", "iss", "aud", "iat",
                    "exp", "jti", "token_type",
                ]
            },
        )

        if payload["token_type"] != "admin_mfa_challenge":
            raise ValueError("Invalid MFA challenge.")

        subject = payload["sub"]

        if (
            not isinstance(subject, str)
            or not subject.isascii()
            or not subject.isdecimal()
            or int(subject) <= 0
            or str(int(subject)) != subject
        ):
            raise ValueError("Invalid MFA challenge.")

        return int(subject)

    except InvalidTokenError as exc:
        raise ValueError(
            "Invalid or expired MFA challenge."
        ) from exc



def get_admin_mfa_version(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={
                "require": [
                    "sub", "iss", "aud", "iat",
                    "exp", "token_type",
                ]
            },
        )
    except InvalidTokenError:
        return None

    version = payload.get("admin_mfa_version")

    if (
        payload.get("token_type") != "access"
        or type(version) is not int
        or version < 1
    ):
        return None

    return version
