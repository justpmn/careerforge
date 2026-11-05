from typing import Literal
from datetime import datetime, timezone
from authlib.integrations.base_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
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

    # Authorization state is no longer needed.
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
