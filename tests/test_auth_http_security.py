
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.backend.app.api.auth import (
    create_csrf_token,
    get_current_user_id,
)
from src.backend.app.core.tokens import create_access_token
from src.backend.app.database.models.admin_mfa import AdminMfaCredential
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db


class FakeDB:
    def __init__(self, state):
        self.state = state

    def get(self, model, user_id):
        user = self.state["user"]

        if model is User:
            return user if user and user.id == user_id else None

        if model is AdminMfaCredential:
            return self.state["mfa"]

        return None


@pytest.fixture
def harness():
    user = SimpleNamespace(
        id=75,
        role="user",
        session_version=2,
        suspended_at=None,
        password_hash="test-hash",
        email_verified_at=datetime.now(timezone.utc),
    )

    state = {"user": user, "mfa": None}
    db = FakeDB(state)
    app = FastAPI()

    @app.get("/private")
    def protected_get(
        user_id: int = Depends(get_current_user_id),
    ):
        return {"user_id": user_id}

    @app.post("/private")
    def protected_post(
        user_id: int = Depends(get_current_user_id),
    ):
        return {"user_id": user_id}

    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as client:
        yield client, state


def token_for(user, mfa_version=None, lifetime=None):
    return create_access_token(
        user_id=user.id,
        session_version=user.session_version,
        admin_mfa_version=mfa_version,
        expires_delta=lifetime,
    )


def set_session(client, token, csrf=False):
    client.cookies.set("careerforge_session", token)

    if csrf:
        csrf_token = create_csrf_token(token)
        client.cookies.set("csrf_token", csrf_token)
        return {"X-CSRF-Token": csrf_token}

    return {}


def enable_admin_mfa(state):
    state["user"].role = "admin"
    state["mfa"] = SimpleNamespace(
        enabled_at=datetime.now(timezone.utc),
        totp_secret_encrypted="test-secret-placeholder",
        mfa_version=2,
    )


def test_missing_session_rejected(harness):
    client, _ = harness

    response = client.get("/private")

    assert response.status_code == 401


def test_invalid_jwt_rejected(harness):
    client, _ = harness
    set_session(client, "not-a-valid-jwt")

    response = client.get("/private")

    assert response.status_code == 401


def test_expired_jwt_rejected(harness):
    client, state = harness

    token = token_for(
        state["user"],
        lifetime=timedelta(seconds=-30),
    )
    set_session(client, token)

    response = client.get("/private")

    assert response.status_code == 401


def test_valid_user_session_accepted(harness):
    client, state = harness
    set_session(client, token_for(state["user"]))

    response = client.get("/private")

    assert response.status_code == 200
    assert response.json()["user_id"] == 75


def test_deleted_user_rejected(harness):
    client, state = harness
    token = token_for(state["user"])
    state["user"] = None

    set_session(client, token)

    assert client.get("/private").status_code == 401


def test_session_version_invalidation(harness):
    client, state = harness
    user = state["user"]

    old_token = token_for(user)
    set_session(client, old_token)

    assert client.get("/private").status_code == 200

    user.session_version += 1

    assert client.get("/private").status_code == 401

    set_session(client, token_for(user))

    assert client.get("/private").status_code == 200


def test_suspended_user_rejected(harness):
    client, state = harness
    user = state["user"]
    set_session(client, token_for(user))

    user.suspended_at = datetime.now(timezone.utc)

    assert client.get("/private").status_code == 403


def test_admin_without_mfa_rejected(harness):
    client, state = harness
    state["user"].role = "admin"

    set_session(client, token_for(state["user"]))

    assert client.get("/private").status_code == 401
    


def test_admin_cannot_bypass_mfa(harness):
    client, state = harness
    enable_admin_mfa(state)

    token = token_for(state["user"])
    set_session(client, token)

    assert client.get("/private").status_code == 401


def test_admin_with_valid_mfa_accepted(harness):
    client, state = harness
    enable_admin_mfa(state)

    token = token_for(state["user"], mfa_version=2)
    set_session(client, token)

    response = client.get("/private")

    assert response.status_code == 200
    assert response.json()["user_id"] == 75


def test_old_mfa_version_rejected(harness):
    client, state = harness
    enable_admin_mfa(state)

    token = token_for(state["user"], mfa_version=1)
    set_session(client, token)

    assert client.get("/private").status_code == 401


def test_missing_csrf_rejected(harness):
    client, state = harness
    set_session(client, token_for(state["user"]))

    response = client.post("/private")

    assert response.status_code == 403


def test_valid_csrf_accepted(harness):
    client, state = harness

    token = token_for(state["user"])
    headers = set_session(client, token, csrf=True)

    response = client.post("/private", headers=headers)

    assert response.status_code == 200


def test_invalid_csrf_rejected(harness):
    client, state = harness

    token = token_for(state["user"])
    set_session(client, token, csrf=True)

    response = client.post(
        "/private",
        headers={"X-CSRF-Token": "invalid-token"},
    )

    assert response.status_code == 403
