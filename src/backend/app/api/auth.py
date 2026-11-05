import hashlib
import hmac
import secrets
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from src.backend.app.core.tokens import (decode_access_token,  get_jwt_secret, get_admin_mfa_version, decode_access_token_version)
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from src.backend.app.database.models.admin_mfa import AdminMfaCredential

bearer_scheme = HTTPBearer(auto_error=False)


def create_csrf_token(session_token: str) -> str:
    nonce = secrets.token_hex(16)
    signature = _csrf_signature(session_token, nonce)
    return f"{nonce}.{signature}"


def _csrf_signature(session_token: str, nonce: str) -> str:
    fingerprint = hashlib.sha256(
        session_token.encode("utf-8")
    ).hexdigest()

    message = f"{fingerprint}.{nonce}".encode("utf-8")

    return hmac.new(
        get_jwt_secret().encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()


def validate_csrf_token(
    request: Request,
    session_token: str,
) -> None:
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")

    forbidden = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid or missing CSRF token.",
    )

    if not cookie_token or not header_token:
        raise forbidden

    if not hmac.compare_digest(cookie_token, header_token):
        raise forbidden

    nonce, separator, signature = cookie_token.partition(".")

    if (
        not separator
        or len(nonce) != 32
        or len(signature) != 64
        or any(c not in "0123456789abcdef" for c in nonce + signature)
    ):
        raise forbidden

    expected = _csrf_signature(session_token, nonce)

    if not hmac.compare_digest(signature, expected):
        raise forbidden


def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> int:

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Existing API clients can continue using Bearer tokens.
    if credentials is not None:
        token = credentials.credentials
        cookie_auth = False
    else:
        token = request.cookies.get("careerforge_session")
        cookie_auth = True

    if not token:
        raise unauthorized

    try:
        user_id = decode_access_token(token)
    except ValueError as exc:
        raise unauthorized from exc

    user = db.get(User, user_id)

    if user is None:
        raise unauthorized

    if user.suspended_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCOUNT_SUSPENDED",
                "message": "This account has been suspended.",
            },
        )

    try:
        token_version = decode_access_token_version(token)
    except ValueError as exc:
        raise unauthorized from exc

    if token_version != user.session_version:
        raise unauthorized


    if user.role == "admin":
        mfa = db.get(AdminMfaCredential, user.id)

        if (
            mfa is None
            or mfa.enabled_at is None
            or mfa.totp_secret_encrypted is None
        ):
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "ADMIN_MFA_ENROLLMENT_REQUIRED",
                    "message": "Set up an authenticator before continuing.",
                },
            )

        if get_admin_mfa_version(token) != mfa.mfa_version:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "ADMIN_MFA_REQUIRED",
                    "message": "Complete administrator MFA authentication.",
                },
            )
        if user.password_hash is not None and user.email_verified_at is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "EMAIL_NOT_VERIFIED",
                    "message": "Please verify your email before continuing.",
                },
            )

        # Cookie-authenticated writes require a CSRF token.
    if cookie_auth and request.method.upper() not in {
            "GET", "HEAD", "OPTIONS"
        }:
            validate_csrf_token(request, token)

    return user.id


def get_admin_enrollment_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> int:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is not None:
        token = credentials.credentials
        cookie_auth = False
    else:
        token = request.cookies.get("careerforge_session")
        cookie_auth = True

    if not token:
        raise unauthorized

    try:
        user_id = decode_access_token(token)
        token_version = decode_access_token_version(token)
    except ValueError as exc:
        raise unauthorized from exc

    user = db.get(User, user_id)

    if user is None:
        raise unauthorized

    if user.suspended_at is not None:
        raise HTTPException(
            status_code=403,
            detail="This account has been suspended.",
        )

    if token_version != user.session_version:
        raise unauthorized

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator account required.",
        )

    if user.email_verified_at is None:
        raise HTTPException(
            status_code=403,
            detail="Verify your email before enrolling MFA.",
        )

    mfa = db.get(AdminMfaCredential, user.id)

    if mfa is not None and (
        mfa.enabled_at is not None
        or mfa.totp_secret_encrypted is not None
    ):
        raise HTTPException(
            status_code=409,
            detail="An authenticator is already enrolled.",
        )

    if cookie_auth and request.method.upper() not in {
        "GET", "HEAD", "OPTIONS"
    }:
        validate_csrf_token(request, token)

    return user.id
