from typing import Literal
from datetime import datetime, timezone
from authlib.integrations.base_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.backend.app.database.models.admin_mfa import AdminMfaCredential
from src.backend.app.api.auth import create_csrf_token
from src.backend.app.core.config import settings
from src.backend.app.core.oauth import oauth
from src.backend.app.core.tokens import create_access_token, create_admin_mfa_challenge_token
from src.backend.app.database.models.oauth_identity import OAuthIdentity
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
import hashlib
import hmac
import time
from pydantic import BaseModel, ConfigDict, Field
from src.backend.app.api.auth import get_current_user_id
from src.backend.app.core.security import verify_password


router = APIRouter(
    prefix="/auth/oauth",
    tags=["OAuth"],
)

Provider = Literal["github", "google"]


def frontend_redirect(error: str | None = None):
    url = f"{settings.oauth_redirect_origin}/auth/callback"

    if error:
        url += f"?error={error}"

    return RedirectResponse(url, status_code=303)


def find_or_create_user(
    db: Session,
    provider: Provider,
    provider_id: str,
    email: str | None,
    name: str,
) -> tuple[User | None, str | None]:

    
    if not isinstance(email, str) or not email.strip():
        return None, "verified_email_required"

    normalized_email = email.strip().lower()

    if len(normalized_email) > 255:
        return None, "verified_email_required"

    identity = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == provider,
            OAuthIdentity.provider_user_id == provider_id,
        )
    )

    if identity:
        user = db.get(User, identity.user_id)

        if user is None:
            return None, "account_unavailable"

        if user.email.strip().lower() != normalized_email:
            return None, "account_email_changed"

        if user.email_verified_at is None:
            user.email_verified_at = datetime.now(timezone.utc)
            db.commit()

        return user, None

    existing_user = db.scalar(
        select(User).where(
            func.lower(func.btrim(User.email)) == normalized_email
        )
    )

    if existing_user:
        return None, "account_exists"

    user = User(
        full_name=(name.strip() or "CareerForge User")[:150],
        email=normalized_email,
        password_hash=None,
        role="user",
        onboarding_completed=False,
        email_verified_at=datetime.now(timezone.utc),
    )
    try:
        db.add(user)
        db.flush()

        db.add(
            OAuthIdentity(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_id,
            )
        )

        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()
        return None, "account_exists"

    return user, None


class GoogleLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str = Field(min_length=1, max_length=128)


def google_link_redirect(result: str) -> RedirectResponse:
    return RedirectResponse(
        f"{settings.oauth_redirect_origin}/settings?google={result}",
        status_code=303,
    )


def valid_google_link_proof(
    request: Request,
    proof: object,
    user_id: int,
) -> bool:
    token = request.cookies.get("careerforge_session")

    if not token or not isinstance(proof, dict):
        return False

    issued_at = proof.get("issued_at")
    fingerprint = proof.get("session_fingerprint")

    if type(proof.get("user_id")) is not int:
        return False

    if type(issued_at) is not int:
        return False

    if not isinstance(fingerprint, str):
        return False

    age = int(time.time()) - issued_at

    if not 0 <= age <= 300:
        return False

    current_fingerprint = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    return (
        proof["user_id"] == user_id
        and hmac.compare_digest(
            current_fingerprint,
            fingerprint,
        )
    )


@router.get("/google/link/status")
def google_link_status(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    identity = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == user_id,
            OAuthIdentity.provider == "google",
        )
    )

    return {"linked": identity is not None}


@router.post("/google/link/prepare")
def prepare_google_link(
    payload: GoogleLinkRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    request.session.pop("cf_google_link", None)
    request.session.pop("cf_google_link_started", None)

    user = db.get(User, user_id)

    if user is None or user.suspended_at is not None:
        raise HTTPException(
            status_code=403,
            detail="Account unavailable.",
        )

    if user.email_verified_at is None:
        raise HTTPException(
            status_code=403,
            detail="Verify your email before linking Google.",
        )

    if user.password_hash is None:
        raise HTTPException(
            status_code=409,
            detail="Password confirmation is required for this linking flow.",
        )

    if not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Password confirmation failed.",
        )

    existing = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == user.id,
            OAuthIdentity.provider == "google",
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Google is already connected to this account.",
        )

    token = request.cookies.get("careerforge_session")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="A browser session is required.",
        )

    request.session["cf_google_link"] = {
        "user_id": user.id,
        "issued_at": int(time.time()),
        "session_fingerprint": hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest(),
    }

    return {"ready": True}


@router.get("/google/link/start")
async def start_google_link(
    request: Request,
    user_id: int = Depends(get_current_user_id),
):
    proof = request.session.get("cf_google_link")

    if not valid_google_link_proof(
        request,
        proof,
        user_id,
    ):
        raise HTTPException(
            status_code=403,
            detail="Confirm your password before connecting Google.",
        )

    if not (
        settings.google_oauth_client_id
        and settings.google_oauth_client_secret
    ):
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured.",
        )

    request.session["cf_google_link_started"] = True

    callback = (
        f"{settings.oauth_redirect_origin}"
        "/api/auth/oauth/google/callback"
    )

    client = oauth.create_client("google")

    return await client.authorize_redirect(
        request,
        callback,
        prompt="select_account",
    )


@router.get("/{provider}/start")
async def start_oauth(provider: Provider, request: Request):

    if provider == "github":
        configured = (
            settings.github_oauth_client_id
            and settings.github_oauth_client_secret
        )
    else:
        configured = (
            settings.google_oauth_client_id
            and settings.google_oauth_client_secret
        )

    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth provider is not configured.",
        )

    callback = (
        f"{settings.oauth_redirect_origin}"
        f"/api/auth/oauth/{provider}/callback"
    )

    client = oauth.create_client(provider)

    return await client.authorize_redirect(request, callback)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: Provider,
    request: Request,
    db: Session = Depends(get_db),
):
    client = oauth.create_client(provider)

    try:
        token = await client.authorize_access_token(request)
    except OAuthError:
        return frontend_redirect("authorization_failed")

    google_link_started = (
        provider == "google"
        and request.session.get("cf_google_link_started") is True
    )

    google_link_proof = request.session.get("cf_google_link")

    request.session.clear()

    if provider == "google":
        profile = token.get("userinfo")

        if not profile or profile.get("email_verified") is not True:
            return frontend_redirect("verified_email_required")

        provider_id = str(profile.get("sub") or "")
        email = profile.get("email")
        name = profile.get("name") or email or "Google User"

    else:
        profile_response = await client.get("user", token=token)
        emails_response = await client.get("user/emails", token=token)

        if (
            profile_response.status_code != 200
            or emails_response.status_code != 200
        ):
            return frontend_redirect("provider_error")

        profile = profile_response.json()
        email_records = emails_response.json()

        email = next(
            (
                item.get("email")
                for item in email_records
                if item.get("primary") is True
                and item.get("verified") is True
            ),
            None,
        )

        provider_id = str(profile.get("id") or "")
        name = (
            profile.get("name")
            or profile.get("login")
            or "GitHub User"
        )

    if not provider_id:
        return frontend_redirect("provider_error")

    if google_link_started:
        try:
            user_id = get_current_user_id(
                request=request,
                credentials=None,
                db=db,
            )
        except HTTPException:
            return google_link_redirect("session_expired")

        if not valid_google_link_proof(
            request,
            google_link_proof,
            user_id,
        ):
            return google_link_redirect("session_expired")

        user = db.scalar(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
        )

        if user is None or user.suspended_at is not None:
            db.rollback()
            return google_link_redirect("account_unavailable")

        if user.email_verified_at is None:
            db.rollback()
            return google_link_redirect("email_unverified")

        if (
            not isinstance(email, str)
            or email.strip().lower() != user.email.strip().lower()
        ):
            db.rollback()
            return google_link_redirect("email_mismatch")

        linked_identity = db.scalar(
            select(OAuthIdentity).where(
                OAuthIdentity.provider == "google",
                OAuthIdentity.provider_user_id == provider_id,
            )
        )

        if linked_identity is not None:
            db.rollback()

            if linked_identity.user_id == user.id:
                return google_link_redirect("linked")

            return google_link_redirect("already_linked")

        account_identity = db.scalar(
            select(OAuthIdentity).where(
                OAuthIdentity.provider == "google",
                OAuthIdentity.user_id == user.id,
            )
        )

        if account_identity is not None:
            db.rollback()
            return google_link_redirect("already_linked")

        try:
            db.add(
                OAuthIdentity(
                    user_id=user.id,
                    provider="google",
                    provider_user_id=provider_id,
                )
            )
            db.commit()
        except IntegrityError:
            db.rollback()
            return google_link_redirect("already_linked")

        return google_link_redirect("linked")


    user, error = find_or_create_user(
        db=db,
        provider=provider,
        provider_id=provider_id,
        email=email,
        name=name,
    )

    if error or user is None:
        return frontend_redirect(error or "provider_error")

    
    if user.role == "admin":
        mfa = db.get(AdminMfaCredential, user.id)

        if (
            mfa is None
            or mfa.enabled_at is None
            or mfa.totp_secret_encrypted is None
        ):
            return frontend_redirect("admin_mfa_enrollment_required")

        challenge_token = create_admin_mfa_challenge_token(user.id)

        response = RedirectResponse(
            f"{settings.oauth_redirect_origin}/auth/mfa",
            status_code=303,
        )

        response.headers["Cache-Control"] = "no-store"

        # Clear any existing full session.
        response.delete_cookie(
            key="careerforge_session",
            path="/api",
        )

        response.set_cookie(
            key="careerforge_admin_mfa_challenge",
            value=challenge_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/api/auth/admin-mfa/challenge",
            max_age=300,
        )

        response.set_cookie(
            key="csrf_token",
            value=create_csrf_token(challenge_token),
            httponly=False,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/",
            max_age=300,
        )

        return response

    access_token = create_access_token(
        user_id=user.id,
        session_version=user.session_version,
    )
    max_age = settings.jwt_access_token_expire_minutes * 60

    response = frontend_redirect()
    
    response.delete_cookie(
    key="careerforge_admin_mfa_challenge",
    path="/api/auth/admin-mfa/challenge",
)

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

    return response
