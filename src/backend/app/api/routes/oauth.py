import hashlib
import hmac
import time
import jwt
from typing import Literal
from datetime import datetime, timezone, timedelta
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
from src.backend.app.core.tokens import (create_access_token,
                                         create_admin_mfa_challenge_token,
                                         JWT_ALGORITHM,
                                         JWT_ISSUER,
                                         JWT_AUDIENCE,
                                         get_jwt_secret)
from src.backend.app.database.models.oauth_identity import OAuthIdentity
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
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



class AccountLinkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Provider
    password: str | None = Field(default=None, max_length=128)


def account_link_redirect(result: str, provider: Provider):
    return RedirectResponse(
        f"{settings.oauth_redirect_origin}/settings"
        f"?account_link={result}&provider={provider}",
        status_code=303,
    )


def recent_oauth_session(request: Request) -> bool:
    token = request.cookies.get("careerforge_session")

    if not token:
        return False

    try:
        claims = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )
    except jwt.InvalidTokenError:
        return False

    issued_at = claims.get("iat")

    return (
        claims.get("token_type") == "access"
        and type(issued_at) is int
        and 0 <= int(time.time()) - issued_at <= 300
    )


def confirm_account_ownership(
    request: Request,
    user: User,
    password: str | None,
) -> None:
    if user.password_hash is not None:
        if (
            not password
            or not verify_password(password, user.password_hash)
        ):
            raise HTTPException(
                status_code=401,
                detail="Password confirmation failed.",
            )
    elif not recent_oauth_session(request):
        raise HTTPException(
            status_code=403,
            detail="Sign in again before changing connected accounts.",
        )


def valid_account_link_proof(
    request: Request,
    proof: object,
    user_id: int,
    provider: Provider,
) -> bool:
    token = request.cookies.get("careerforge_session")

    if not token or not isinstance(proof, dict):
        return False

    issued_at = proof.get("issued_at")
    fingerprint = proof.get("session_fingerprint")

    if (
        type(proof.get("user_id")) is not int
        or type(issued_at) is not int
        or not isinstance(fingerprint, str)
        or proof.get("provider") != provider
    ):
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


@router.get("/link/status")
def connected_account_status(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    providers = set(
        db.scalars(
            select(OAuthIdentity.provider).where(
                OAuthIdentity.user_id == user_id
            )
        ).all()
    )

    return {
        "google": "google" in providers,
        "github": "github" in providers,
        "has_password": user.password_hash is not None,
    }


@router.post("/link/disconnect")
def disconnect_account(
    payload: AccountLinkRequest,
    request: Request,
    response: Response,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"

    user = db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
    )

    if user is None or user.suspended_at is not None:
        raise HTTPException(
            status_code=403,
            detail="Account unavailable.",
        )

    identities = db.scalars(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == user.id
        )
    ).all()

    identity = next(
        (
            item for item in identities
            if item.provider == payload.provider
        ),
        None,
    )

    if identity is None:
        raise HTTPException(
            status_code=404,
            detail="This provider is not connected.",
        )

    remaining_providers = {
        item.provider for item in identities
        if item.provider != payload.provider
    }

    if user.password_hash is None and not remaining_providers:
        raise HTTPException(
            status_code=409,
            detail="You cannot disconnect your only sign-in method.",
        )

    confirm_account_ownership(
        request,
        user,
        payload.password,
    )

    db.delete(identity)
    user.session_version = (user.session_version or 0) + 1
    db.commit()

    request.session.clear()

    response.delete_cookie(
        key="careerforge_session",
        path="/api",
    )

    response.delete_cookie(
        key="csrf_token",
        path="/",
    )

    response.delete_cookie(
        key="careerforge_admin_mfa_challenge",
        path="/api/auth/admin-mfa/challenge",
    )

    return {
        "disconnected": payload.provider,
        "signed_out": True,
    }


@router.post("/link/prepare")
def prepare_account_link(
    payload: AccountLinkRequest,
    request: Request,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    request.session.pop("cf_oauth_link", None)
    request.session.pop("cf_oauth_link_started", None)

    user = db.get(User, user_id)

    if user is None or user.suspended_at is not None:
        raise HTTPException(
            status_code=403,
            detail="Account unavailable.",
        )

    if user.email_verified_at is None:
        raise HTTPException(
            status_code=403,
            detail="Verify your email before linking an account.",
        )

    confirm_account_ownership(
        request,
        user,
        payload.password,
    )

    existing = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == user.id,
            OAuthIdentity.provider == payload.provider,
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This provider is already connected.",
        )

    token = request.cookies.get("careerforge_session")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="A browser session is required.",
        )

    request.session["cf_oauth_link"] = {
        "user_id": user.id,
        "provider": payload.provider,
        "issued_at": int(time.time()),
        "session_fingerprint": hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest(),
    }

    return {"ready": True}


@router.get("/{provider}/link/start")
async def start_account_link(
    provider: Provider,
    request: Request,
    user_id: int = Depends(get_current_user_id),
):
    proof = request.session.get("cf_oauth_link")

    if not valid_account_link_proof(
        request,
        proof,
        user_id,
        provider,
    ):
        raise HTTPException(
            status_code=403,
            detail="Confirm your account before linking a provider.",
        )

    if provider == "google":
        configured = (
            settings.google_oauth_client_id
            and settings.google_oauth_client_secret
        )
    else:
        configured = (
            settings.github_oauth_client_id
            and settings.github_oauth_client_secret
        )

    if not configured:
        raise HTTPException(
            status_code=503,
            detail="OAuth provider is not configured.",
        )

    request.session["cf_oauth_link_started"] = provider

    callback = (
        f"{settings.oauth_redirect_origin}"
        f"/api/auth/oauth/{provider}/callback"
    )

    client = oauth.create_client(provider)

    return await client.authorize_redirect(
        request,
        callback,
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

    account_link_started = request.session.get(
    "cf_oauth_link_started"
    )
    account_link_proof = request.session.get("cf_oauth_link")

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


    if account_link_started is not None:
        if account_link_started != provider:
            return account_link_redirect(
                "authorization_failed",
                provider,
            )

        try:
            user_id = get_current_user_id(
                request=request,
                credentials=None,
                db=db,
            )
        except HTTPException:
            return account_link_redirect(
                "session_expired",
                provider,
            )

        if not valid_account_link_proof(
            request,
            account_link_proof,
            user_id,
            provider,
        ):
            return account_link_redirect(
                "session_expired",
                provider,
            )

        user = db.scalar(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
        )

        if user is None or user.suspended_at is not None:
            db.rollback()
            return account_link_redirect(
                "account_unavailable",
                provider,
            )

        if user.email_verified_at is None:
            db.rollback()
            return account_link_redirect(
                "email_unverified",
                provider,
            )

        if (
            not isinstance(email, str)
            or email.strip().lower() != user.email.strip().lower()
        ):
            db.rollback()
            return account_link_redirect(
                "email_mismatch",
                provider,
            )

        linked_identity = db.scalar(
            select(OAuthIdentity).where(
                OAuthIdentity.provider == provider,
                OAuthIdentity.provider_user_id == provider_id,
            )
        )

        if linked_identity is not None:
            db.rollback()

            if linked_identity.user_id == user.id:
                return account_link_redirect("linked", provider)

            return account_link_redirect(
                "already_linked",
                provider,
            )

        account_identity = db.scalar(
            select(OAuthIdentity).where(
                OAuthIdentity.provider == provider,
                OAuthIdentity.user_id == user.id,
            )
        )

        if account_identity is not None:
            db.rollback()
            return account_link_redirect(
                "already_linked",
                provider,
            )

        try:
            db.add(
                OAuthIdentity(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=provider_id,
                )
            )
            db.commit()
        except IntegrityError:
            db.rollback()
            return account_link_redirect(
                "already_linked",
                provider,
            )

        return account_link_redirect("linked", provider)


    user, error = find_or_create_user(
        db=db,
        provider=provider,
        provider_id=provider_id,
        email=email,
        name=name,
    )

    if error or user is None:
        return frontend_redirect(error or "provider_error")

    
    if user.suspended_at is not None:
        return frontend_redirect("account_unavailable")

    if user.role == "admin":
        mfa = db.get(AdminMfaCredential, user.id)

        if (
            mfa is None
            or mfa.enabled_at is None
            or mfa.totp_secret_encrypted is None
        ):
            if user.password_hash is not None:
                return frontend_redirect("admin_mfa_enrollment_required")

            enrollment_token = create_access_token(
                user_id=user.id,
                session_version=user.session_version,
                expires_delta=timedelta(minutes=15),
            )

            request.session["cf_mfa_oauth_approved"] = {
                "user_id": user.id,
                "provider": provider,
                "verified_at": int(time.time()),
            }
            linked_providers = set(
                db.scalars(
                    select(OAuthIdentity.provider).where(
                        OAuthIdentity.user_id == user.id,
                        OAuthIdentity.provider.in_(("google", "github")),
                    )
                ).all()
            )

            display_provider = (
                "both"
                if {"google", "github"}.issubset(linked_providers)
                else provider
            )
            response = RedirectResponse(
                f"{settings.oauth_redirect_origin}/auth/mfa?enroll=1&oauth={display_provider}",
                status_code=303,
            )
            response.headers["Cache-Control"] = "no-store"

            response.set_cookie(
                key="careerforge_session",
                value=enrollment_token,
                httponly=True,
                secure=settings.cookie_secure,
                samesite="lax",
                path="/api",
                max_age=900,
            )

            response.set_cookie(
                key="csrf_token",
                value=create_csrf_token(enrollment_token),
                httponly=False,
                secure=settings.cookie_secure,
                samesite="lax",
                path="/",
                max_age=900,
            )

            response.delete_cookie(
                key="careerforge_admin_mfa_challenge",
                path="/api/auth/admin-mfa/challenge",
            )

            return response

        challenge_token = create_admin_mfa_challenge_token(user.id)

        response = RedirectResponse(
            f"{settings.oauth_redirect_origin}/auth/mfa",
            status_code=303,
        )
        response.headers["Cache-Control"] = "no-store"

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
    response.headers["Cache-Control"] = "no-store"

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
