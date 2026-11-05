
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, select, func
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from src.backend.app.api.auth import create_csrf_token
from src.backend.app.api.routes import oauth
from src.backend.app.core.security import hash_password
from src.backend.app.core.tokens import create_access_token
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from datetime import timedelta
from types import SimpleNamespace
from authlib.integrations.base_client import OAuthError


OAuthIdentity = oauth.OAuthIdentity


@pytest.fixture(scope="module")
def engine():
    raw_url = os.getenv("CAREERFORGE_TEST_DATABASE_URL")

    if not raw_url:
        pytest.skip("Set CAREERFORGE_TEST_DATABASE_URL first.")

    url = make_url(raw_url)

    if (
        url.get_backend_name() != "postgresql"
        or url.database != "careerforge_test"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
    ):
        pytest.fail(
            "Integration tests require local PostgreSQL "
            "database careerforge_test."
        )

    db_engine = create_engine(raw_url, pool_pre_ping=True)

    try:
        yield db_engine
    finally:
        db_engine.dispose()


@pytest.fixture
def db(engine):
    with engine.connect() as connection:
        transaction = connection.begin()

        session = Session(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def app(db):
    application = FastAPI()
    application.add_middleware(
        SessionMiddleware,
        secret_key="test-session-secret-not-for-production",
    )
    application.include_router(oauth.router, prefix="/api")
    application.dependency_overrides[get_db] = lambda: db

    yield application

    application.dependency_overrides.clear()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def route(app, name):
    return str(app.url_path_for(name))


def create_user(db, password_hash=None):
    user = User(
        full_name="Regression Test User",
        email=f"cf-test-{uuid4().hex}@example.invalid",
        password_hash=password_hash,
        role="user",
        email_verified_at=datetime.now(timezone.utc),
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def add_identity(db, user, provider, subject=None):
    identity = OAuthIdentity(
        user_id=user.id,
        provider=provider,
        provider_user_id=subject or f"{provider}-{uuid4().hex}",
    )

    db.add(identity)
    db.commit()
    return identity

def sign_in(client, user):
    token = create_access_token(
        user_id=user.id,
        session_version=user.session_version,
    )

    csrf = create_csrf_token(token)

    client.cookies.set(
        "careerforge_session", token, path="/api"
    )
    client.cookies.set("csrf_token", csrf, path="/")

    return token, {"X-CSRF-Token": csrf}


def identities_for(db, user):
    return db.scalars(
        select(OAuthIdentity).where(
            OAuthIdentity.user_id == user.id
        )
    ).all()


def test_provider_identity_cannot_belong_to_two_users(db):
    first = create_user(db)
    second = create_user(db)
    subject = f"github-{uuid4().hex}"

    add_identity(db, first, "github", subject)

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(OAuthIdentity(
                user_id=second.id,
                provider="github",
                provider_user_id=subject,
            ))
            db.flush()

    assert len(identities_for(db, first)) == 1
    assert identities_for(db, second) == []


def test_normalized_email_uniqueness(db):
    user = create_user(db)

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(User(
                full_name="Duplicate Account",
                email=user.email.upper(),
                role="user",
                password_hash=None,
            ))
            db.flush()


def test_connected_accounts_status_uses_database(
    app, client, db
):
    user = create_user(db)
    add_identity(db, user, "github")
    sign_in(client, user)

    response = client.get(
        route(app, "connected_account_status")
    )

    assert response.status_code == 200
    assert response.json() == {
        "google": False,
        "github": True,
        "has_password": False,
    }


def test_last_sign_in_method_cannot_be_removed(
    app, client, db
):
    user = create_user(db)
    add_identity(db, user, "github")
    _, headers = sign_in(client, user)

    response = client.post(
        route(app, "disconnect_account"),
        json={"provider": "github"},
        headers=headers,
    )

    assert response.status_code == 409
    assert len(identities_for(db, user)) == 1


def test_disconnect_requires_csrf(app, client, db):
    user = create_user(db)
    add_identity(db, user, "google")
    add_identity(db, user, "github")
    sign_in(client, user)

    path = route(app, "disconnect_account")

    assert client.post(
        path, json={"provider": "google"}
    ).status_code == 403

    assert client.post(
        path,
        json={"provider": "google"},
        headers={"X-CSRF-Token": "invalid"},
    ).status_code == 403

    assert len(identities_for(db, user)) == 2


def test_disconnection_revokes_old_session(
    app, client, db
):
    user = create_user(db)
    add_identity(db, user, "google")
    add_identity(db, user, "github")

    old_version = user.session_version
    old_token, headers = sign_in(client, user)

    status_path = route(app, "connected_account_status")
    disconnect_path = route(app, "disconnect_account")

    assert client.get(status_path).status_code == 200

    response = client.post(
        disconnect_path,
        json={"provider": "google"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["disconnected"] == "google"

    db.expire_all()
    db.refresh(user)

    assert user.session_version == old_version + 1
    assert {item.provider for item in identities_for(db, user)} == {
        "github"
    }

    client.cookies.set(
        "careerforge_session", old_token, path="/api"
    )

    assert client.get(status_path).status_code == 401

    sign_in(client, user)

    new_status = client.get(status_path)

    assert new_status.status_code == 200
    assert new_status.json()["github"] is True
    assert new_status.json()["google"] is False


def test_user_cannot_disconnect_another_users_provider(
    app, client, db
):
    first = create_user(db)
    second = create_user(db)

    add_identity(db, first, "github")
    add_identity(db, second, "google")

    _, headers = sign_in(client, first)

    response = client.post(
        route(app, "disconnect_account"),
        json={"provider": "google"},
        headers=headers,
    )

    assert response.status_code == 404
    assert {item.provider for item in identities_for(db, second)} == {
        "google"
    }


def test_password_confirmation_required_to_disconnect(
    app, client, db
):
    password = "Regression-Test-Password-2026!"
    user = create_user(db, hash_password(password))
    add_identity(db, user, "google")
    _, headers = sign_in(client, user)

    path = route(app, "disconnect_account")

    wrong = client.post(
        path,
        json={
            "provider": "google",
            "password": "incorrect-password",
        },
        headers=headers,
    )

    assert wrong.status_code == 401
    assert len(identities_for(db, user)) == 1

    correct = client.post(
        path,
        json={"provider": "google", "password": password},
        headers=headers,
    )

    assert correct.status_code == 200
    assert identities_for(db, user) == []


class StubOAuthProvider:
    def __init__(self, provider, profile, emails=None, denied=False):
        self.provider = provider
        self.profile = profile
        self.emails = emails or []
        self.denied = denied

    async def authorize_redirect(self, request, redirect_uri):
        return RedirectResponse("/mock-provider", status_code=302)

    async def authorize_access_token(self, request):
        if self.denied:
            raise OAuthError(error="access_denied")

        if self.provider == "google":
            return {"userinfo": self.profile}

        return {"access_token": "mock-access-token"}

    async def get(self, endpoint, token=None):
        data = self.profile if endpoint == "user" else self.emails
        return SimpleNamespace(status_code=200, json=lambda: data)


def mock_oauth(monkeypatch, provider, profile, emails=None, denied=False):
    stub = StubOAuthProvider(provider, profile, emails, denied)

    monkeypatch.setattr(
        oauth.oauth, "create_client", lambda requested: stub
    )
    monkeypatch.setattr(
        oauth.settings, f"{provider}_oauth_client_id", "test-client-id"
    )
    monkeypatch.setattr(
        oauth.settings, f"{provider}_oauth_client_secret", "test-client-secret"
    )

    return stub


def google_profile(email, subject=None, verified=True):
    return {
        "sub": subject or f"google-{uuid4().hex}",
        "email": email,
        "email_verified": verified,
        "name": "OAuth Regression User",
    }


def callback_url(app, provider):
    return str(app.url_path_for("oauth_callback", provider=provider))


def begin_google_link(app, client, user):
    _, headers = sign_in(client, user)

    response = client.post(
        str(app.url_path_for("prepare_account_link")),
        json={"provider": "google"},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["ready"] is True

    response = client.get(
        str(app.url_path_for("start_account_link", provider="google")),
        follow_redirects=False,
    )

    assert response.status_code in (302, 303), response.text


def test_google_callback_rejects_unverified_email(
    app, client, db, monkeypatch
):
    before = db.scalar(select(func.count()).select_from(User))

    mock_oauth(
        monkeypatch,
        "google",
        google_profile("unverified@example.invalid", verified=False),
    )

    response = client.get(
        callback_url(app, "google"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "error=verified_email_required" in response.headers["location"]
    assert db.scalar(select(func.count()).select_from(User)) == before


def test_google_callback_blocks_existing_email_account(
    app, client, db, monkeypatch
):
    user = create_user(db)

    mock_oauth(
        monkeypatch, "google", google_profile(user.email)
    )

    response = client.get(
        callback_url(app, "google"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "error=account_exists" in response.headers["location"]
    assert identities_for(db, user) == []


def test_google_callback_rejects_changed_identity_email(
    app, client, db, monkeypatch
):
    user = create_user(db)
    subject = f"google-{uuid4().hex}"
    add_identity(db, user, "google", subject)

    mock_oauth(
        monkeypatch,
        "google",
        google_profile("different@example.invalid", subject),
    )

    response = client.get(
        callback_url(app, "google"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "error=account_email_changed" in response.headers["location"]
    assert len(identities_for(db, user)) == 1


def test_github_callback_requires_primary_verified_email(
    app, client, db, monkeypatch
):
    before = db.scalar(
        select(func.count()).select_from(OAuthIdentity)
    )

    mock_oauth(
        monkeypatch,
        "github",
        {"id": f"github-{uuid4().hex}", "login": "test-user"},
        emails=[
            {
                "email": "primary@example.invalid",
                "primary": True,
                "verified": False,
            },
            {
                "email": "secondary@example.invalid",
                "primary": False,
                "verified": True,
            },
        ],
    )

    response = client.get(
        callback_url(app, "github"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "error=verified_email_required" in response.headers["location"]
    assert db.scalar(
        select(func.count()).select_from(OAuthIdentity)
    ) == before


def test_oauth_authorization_failure_is_rejected(
    app, client, db, monkeypatch
):
    before = db.scalar(select(func.count()).select_from(User))

    mock_oauth(
        monkeypatch, "google", {}, denied=True
    )

    response = client.get(
        callback_url(app, "google"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "error=authorization_failed" in response.headers["location"]
    assert db.scalar(select(func.count()).select_from(User)) == before


def test_google_callback_creates_new_account_and_identity(
    app, client, db, monkeypatch
):
    email = f"new-oauth-{uuid4().hex}@example.invalid"
    subject = f"google-{uuid4().hex}"

    mock_oauth(
        monkeypatch,
        "google",
        google_profile(email, subject),
    )

    response = client.get(
        callback_url(app, "google"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "error=" not in response.headers["location"]

    identity = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == "google",
            OAuthIdentity.provider_user_id == subject,
        )
    )

    assert identity is not None

    user = db.get(User, identity.user_id)

    assert user.email == email
    assert user.password_hash is None
    assert user.email_verified_at is not None
    assert response.cookies.get("careerforge_session")


def test_link_callback_rejects_email_mismatch(
    app, client, db, monkeypatch
):
    user = create_user(db)

    mock_oauth(
        monkeypatch,
        "google",
        google_profile("wrong-email@example.invalid"),
    )

    begin_google_link(app, client, user)

    response = client.get(
        callback_url(app, "google"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "account_link=email_mismatch" in response.headers["location"]
    assert identities_for(db, user) == []


def test_link_callback_cannot_take_another_users_identity(
    app, client, db, monkeypatch
):
    first = create_user(db)
    second = create_user(db)

    subject = f"google-{uuid4().hex}"
    add_identity(db, second, "google", subject)

    mock_oauth(
        monkeypatch,
        "google",
        google_profile(first.email, subject),
    )

    begin_google_link(app, client, first)

    response = client.get(
        callback_url(app, "google"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "account_link=already_linked" in response.headers["location"]
    assert identities_for(db, first) == []

    existing = db.scalar(
        select(OAuthIdentity).where(
            OAuthIdentity.provider == "google",
            OAuthIdentity.provider_user_id == subject,
        )
    )

    assert existing.user_id == second.id


def test_link_callback_rejects_changed_session(
    app, client, db, monkeypatch
):
    user = create_user(db)

    mock_oauth(
        monkeypatch,
        "google",
        google_profile(user.email),
    )

    begin_google_link(app, client, user)

    replacement = create_access_token(
        user_id=user.id,
        session_version=user.session_version,
        expires_delta=timedelta(hours=5, minutes=1),
    )

    client.cookies.set(
        "careerforge_session", replacement, path="/api"
    )

    response = client.get(
        callback_url(app, "google"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "account_link=session_expired" in response.headers["location"]
    assert identities_for(db, user) == []


def test_link_callback_connects_verified_provider(
    app, client, db, monkeypatch
):
    user = create_user(db)
    subject = f"google-{uuid4().hex}"

    mock_oauth(
        monkeypatch,
        "google",
        google_profile(user.email, subject),
    )

    begin_google_link(app, client, user)

    response = client.get(
        callback_url(app, "google"), follow_redirects=False
    )

    assert response.status_code == 303
    assert "account_link=linked" in response.headers["location"]

    identities = identities_for(db, user)

    assert len(identities) == 1
    assert identities[0].provider == "google"
    assert identities[0].provider_user_id == subject

    status_response = client.get(
        str(app.url_path_for("connected_account_status"))
    )

    assert status_response.status_code == 200
    assert status_response.json()["google"] is True
