import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
import json
import time
from authlib.integrations.base_client import OAuthError
from fastapi.responses import RedirectResponse
from src.backend.app.core.config import settings
from src.backend.app.core.oauth import oauth
from src.backend.app.database.models.oauth_identity import OAuthIdentity
import pyotp
from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from src.backend.app.api.admin_auth import require_admin
from src.backend.app.core.security import verify_password
from src.backend.app.database.models.admin_mfa import (AdminMfaCredential, AdminMfaRecoveryCode)
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from src.backend.app.services.admin_totp import ( decrypt_totp_secret, encrypt_totp_secret, generate_totp_secret, get_totp_provisioning_uri)
from src.backend.app.api.auth import create_csrf_token, validate_csrf_token
from src.backend.app.core.config import settings
from src.backend.app.core.tokens import (create_access_token, decode_admin_mfa_challenge_token)
from src.backend.app.services.admin_mfa_verification import (verify_and_consume_admin_totp)
from src.backend.app.services.mfa_qr import build_totp_qr_data_url
from src.backend.app.api.admin_auth import require_admin_enrollment

router = APIRouter(
    prefix="/auth/admin-mfa",
    tags=["Admin MFA"],
)

ENROLLMENT_LIFETIME = timedelta(minutes=10)
LOCKOUT_DURATION = timedelta(minutes=15)
MAX_ATTEMPTS = 5


class StartEnrollmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str | None = Field(default=None, min_length=1, max_length=128)

class ConfirmEnrollmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(pattern=r"^[0-9]{6}$")

class ReplaceAuthenticatorRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_code: str = Field(pattern=r"^[0-9]{6}$")

class EnrollmentStartResponse(BaseModel):
    provisioning_uri: str
    expires_at: datetime
    qr_code_data_url: str


class EnrollmentConfirmResponse(BaseModel):
    message: str
    recovery_codes: list[str]

class VerifyAdminChallengeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(pattern=r"^[0-9]{6}$")

def matching_totp_step(
    secret: str,
    code: str,
    now: datetime,
) -> int | None:
    totp = pyotp.TOTP(secret)
    current_step = int(now.timestamp()) // totp.interval

    matches = [
        step
        for step in (current_step - 1, current_step, current_step + 1)
        if step >= 0
        and hmac.compare_digest(
            totp.at(step * totp.interval),
            code,
        )
    ]

    return max(matches) if matches else None


@router.get("/enroll/google/start")
async def start_google_enrollment(
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    identity = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == admin.id,
            OAuthIdentity.provider == "google",
        )
    )

    if identity is None:
        raise HTTPException(
            status_code=403,
            detail="A linked Google account is required.",
        )

    record = db.get(AdminMfaCredential, admin.id)

    if record and record.enabled_at is not None:
        raise HTTPException(
            status_code=409,
            detail="Authenticator already enrolled.",
        )

    if not (
        settings.google_oauth_client_id
        and settings.google_oauth_client_secret
    ):
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured.",
        )

    request.session.pop("cf_mfa_google_approved", None)
    request.session["cf_mfa_google_pending"] = {
        "user_id": admin.id,
        "started_at": int(time.time()),
    }

    callback = (
        f"{settings.oauth_redirect_origin}"
        "/api/auth/admin-mfa/enroll/google/callback"
    )

    client = oauth.create_client("google")

    return await client.authorize_redirect(
        request,
        callback,
        max_age=0,
        prompt="select_account",
        claims=json.dumps({
            "id_token": {
                "auth_time": {"essential": True}
            }
        }),
    )


@router.get("/enroll/google/callback")
async def complete_google_enrollment_auth(
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    pending = request.session.pop(
        "cf_mfa_google_pending", None
    )

    now = int(time.time())

    if (
        not isinstance(pending, dict)
        or pending.get("user_id") != admin.id
        or type(pending.get("started_at")) is not int
        or not 0 <= now - pending["started_at"] <= 300
    ):
        raise HTTPException(
            status_code=403,
            detail="Google reauthentication request expired.",
        )

    client = oauth.create_client("google")

    try:
        token = await client.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(
            status_code=403,
            detail="Google reauthentication failed.",
        ) from exc

    profile = token.get("userinfo") or {}
    auth_time = profile.get("auth_time")

    identity = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == admin.id,
            OAuthIdentity.provider == "google",
            OAuthIdentity.provider_user_id == str(
                profile.get("sub") or ""
            ),
        )
    )

    valid = (
        identity is not None
        and profile.get("email_verified") is True
        and isinstance(profile.get("email"), str)
        and profile["email"].strip().lower()
            == admin.email.strip().lower()
        and type(auth_time) is int
        and pending["started_at"] - 60 <= auth_time <= now + 60
        and now - auth_time <= 120
    )

    if not valid:
        raise HTTPException(
            status_code=403,
            detail="Fresh Google authentication could not be verified.",
        )

    request.session["cf_mfa_google_approved"] = {
        "user_id": admin.id,
        "verified_at": now,
    }

    response = RedirectResponse(
        f"{settings.oauth_redirect_origin}/admin?mfa_setup=ready",
        status_code=303,
    )
    response.headers["Cache-Control"] = "no-store"
    return response

@router.post(
    "/enroll/start",
    response_model=EnrollmentStartResponse,
)

def start_enrollment(
    payload: StartEnrollmentRequest,
    request: Request,
    response: Response,
    admin: User = Depends(require_admin_enrollment),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"

    if admin.password_hash is not None:
        if (
            not payload.password
            or not verify_password(
                payload.password,
                admin.password_hash,
            )
        ):
            raise HTTPException(
                status_code=401,
                detail="Password confirmation failed.",
            )
    else:
        proof = request.session.get("cf_mfa_google_approved")
        now_ts = int(time.time())

        if (
            not isinstance(proof, dict)
            or proof.get("user_id") != admin.id
            or type(proof.get("verified_at")) is not int
            or not 0 <= now_ts - proof["verified_at"] <= 300
        ):
            raise HTTPException(
                status_code=403,
                detail="Reauthenticate with Google before enrollment.",
            )

        request.session.pop("cf_mfa_google_approved", None)

    now = datetime.now(timezone.utc)

    record = db.scalar(
        select(AdminMfaCredential)
        .where(AdminMfaCredential.user_id == admin.id)
        .with_for_update()
    )

    if record and record.enabled_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An authenticator is already enrolled.",
        )

    if record and record.locked_until and record.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
        )

    secret = generate_totp_secret()
    expires_at = now + ENROLLMENT_LIFETIME

    if record is None:
        record = AdminMfaCredential(user_id=admin.id)
        db.add(record)

    record.pending_secret_encrypted = encrypt_totp_secret(secret)
    record.pending_expires_at = expires_at
    record.failed_attempts = 0
    record.locked_until = None

    provisioning_uri = get_totp_provisioning_uri(
        secret,
        admin.email,
    )

    qr_code_data_url = build_totp_qr_data_url(
        provisioning_uri
    )

    db.commit()

    return EnrollmentStartResponse(
        provisioning_uri=provisioning_uri,
        qr_code_data_url=qr_code_data_url,
        expires_at=expires_at,
    )

@router.post(
    "/enroll/confirm",
    response_model=EnrollmentConfirmResponse,
)
def confirm_enrollment(
    payload: ConfirmEnrollmentRequest,
    response: Response,
    admin: User = Depends(require_admin_enrollment),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    now = datetime.now(timezone.utc)

    record = db.scalar(
        select(AdminMfaCredential)
        .where(AdminMfaCredential.user_id == admin.id)
        .with_for_update()
    )

    if record is None or record.pending_secret_encrypted is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start authenticator enrollment first.",
        )

    if record.enabled_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An authenticator is already enrolled.",
        )

    if (
        record.pending_expires_at is None
        or record.pending_expires_at <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enrollment expired. Start again.",
        )

    if record.locked_until and record.locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again later.",
        )

    secret = decrypt_totp_secret(record.pending_secret_encrypted)
    matched_step = matching_totp_step(secret, payload.code, now)

    if matched_step is None:
        record.failed_attempts += 1

        if record.failed_attempts >= MAX_ATTEMPTS:
            record.locked_until = now + LOCKOUT_DURATION

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authenticator code.",
        )

    recovery_codes = [
        secrets.token_hex(16)
        for _ in range(8)
    ]

    for code in recovery_codes:
        db.add(
            AdminMfaRecoveryCode(
                user_id=admin.id,
                code_hash=hashlib.sha256(
                    code.encode("ascii")
                ).hexdigest(),
            )
        )

    record.totp_secret_encrypted = record.pending_secret_encrypted
    record.pending_secret_encrypted = None
    record.pending_expires_at = None
    record.enabled_at = now
    record.last_accepted_step = matched_step
    record.failed_attempts = 0
    record.locked_until = None
    record.mfa_version += 1

    db.commit()

    return EnrollmentConfirmResponse(
        message="Authenticator enrollment completed.",
        recovery_codes=recovery_codes,
    )


@router.post("/challenge/verify")
def verify_admin_challenge(
    payload: VerifyAdminChallengeRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"

    challenge_token = request.cookies.get(
        "careerforge_admin_mfa_challenge"
    )

    if not challenge_token:
        raise HTTPException(
            status_code=401,
            detail="Administrator MFA challenge required.",
        )

    try:
        user_id = decode_admin_mfa_challenge_token(
            challenge_token
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired MFA challenge.",
        ) from exc

    validate_csrf_token(request, challenge_token)

    user = db.get(User, user_id)

    if user is None or user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required.",
        )

    if user.email_verified_at is None:
        raise HTTPException(
            status_code=403,
            detail="Email verification required.",
        )

    mfa_version = verify_and_consume_admin_totp(
        db=db,
        user_id=user.id,
        code=payload.code,
    )

    access_token = create_access_token(
        user_id=user.id,
        admin_mfa_version=mfa_version,
        session_version=user.session_version,
    )

    max_age = settings.jwt_access_token_expire_minutes * 60

    response.set_cookie(
        key="careerforge_session",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/api",
        max_age=max_age,
    )

    response.set_cookie(
        key="csrf_token",
        value=create_csrf_token(access_token),
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=max_age,
    )

    response.delete_cookie(
        key="careerforge_admin_mfa_challenge",
        path="/api/auth/admin-mfa/challenge",
    )

    return {
        "message": "Administrator MFA verified.",
    }


@router.post(
    "/replace/start",
    response_model=EnrollmentStartResponse,
)
def start_authenticator_replacement(
    payload: ReplaceAuthenticatorRequest,
    response: Response,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    now = datetime.now(timezone.utc)

    record = db.scalar(
        select(AdminMfaCredential)
        .where(AdminMfaCredential.user_id == admin.id)
        .with_for_update()
    )

    if (
        record is None
        or record.enabled_at is None
        or record.totp_secret_encrypted is None
    ):
        raise HTTPException(
            status_code=409,
            detail="No active authenticator is enrolled.",
        )

    if record.locked_until and record.locked_until > now:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
        )

    current_secret = decrypt_totp_secret(
        record.totp_secret_encrypted
    )

    matched_step = matching_totp_step(
        current_secret,
        payload.current_code,
        now,
    )

    reused = (
        matched_step is not None
        and record.last_accepted_step is not None
        and matched_step <= record.last_accepted_step
    )

    if matched_step is None or reused:
        record.failed_attempts += 1

        if record.failed_attempts >= MAX_ATTEMPTS:
            record.locked_until = now + LOCKOUT_DURATION

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid or previously used authenticator code.",
        )

    new_secret = generate_totp_secret()
    expires_at = now + ENROLLMENT_LIFETIME

    record.last_accepted_step = matched_step
    record.pending_secret_encrypted = encrypt_totp_secret(new_secret)
    record.pending_expires_at = expires_at
    record.failed_attempts = 0
    record.locked_until = None

    provisioning_uri = get_totp_provisioning_uri(
        new_secret,
        admin.email,
    )

    qr_code_data_url = build_totp_qr_data_url(
        provisioning_uri
    )

    db.commit()

    return EnrollmentStartResponse(
        provisioning_uri=provisioning_uri,
        qr_code_data_url=qr_code_data_url,
        expires_at=expires_at,
    )


@router.post(
    "/replace/confirm",
    response_model=EnrollmentConfirmResponse,
)
def confirm_authenticator_replacement(
    payload: ConfirmEnrollmentRequest,
    response: Response,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    now = datetime.now(timezone.utc)

    record = db.scalar(
        select(AdminMfaCredential)
        .where(AdminMfaCredential.user_id == admin.id)
        .with_for_update()
    )

    if (
        record is None
        or record.enabled_at is None
        or record.totp_secret_encrypted is None
        or record.pending_secret_encrypted is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Start authenticator replacement first.",
        )

    if (
        record.pending_expires_at is None
        or record.pending_expires_at <= now
    ):
        raise HTTPException(
            status_code=400,
            detail="Replacement expired. Start again.",
        )

    if record.locked_until and record.locked_until > now:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
        )

    new_secret = decrypt_totp_secret(
        record.pending_secret_encrypted
    )

    matched_step = matching_totp_step(
        new_secret,
        payload.code,
        now,
    )

    if matched_step is None:
        record.failed_attempts += 1

        if record.failed_attempts >= MAX_ATTEMPTS:
            record.locked_until = now + LOCKOUT_DURATION

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid replacement authenticator code.",
        )

    recovery_codes = [
        secrets.token_hex(16)
        for _ in range(8)
    ]

    db.execute(
        delete(AdminMfaRecoveryCode).where(
            AdminMfaRecoveryCode.user_id == admin.id
        )
    )

    for code in recovery_codes:
        db.add(
            AdminMfaRecoveryCode(
                user_id=admin.id,
                code_hash=hashlib.sha256(
                    code.encode("ascii")
                ).hexdigest(),
            )
        )

    record.totp_secret_encrypted = record.pending_secret_encrypted
    record.pending_secret_encrypted = None
    record.pending_expires_at = None
    record.enabled_at = now
    record.last_accepted_step = matched_step
    record.failed_attempts = 0
    record.locked_until = None
    record.mfa_version += 1

    db.commit()

    return EnrollmentConfirmResponse(
        message="Authenticator replaced successfully.",
        recovery_codes=recovery_codes,
    )
