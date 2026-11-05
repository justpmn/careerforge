
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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
