
import hashlib
import importlib
import time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

oauth = importlib.import_module("src.backend.app.api.routes.oauth")


class FakeResult:
    def __init__(self, items):
        self.items = items

    def all(self):
        return self.items


class FakeDB:
    def __init__(self, user, providers):
        self.user = user
        self.identities = [
            SimpleNamespace(user_id=user.id, provider=provider)
            for provider in providers
        ]
        self.deleted = []
        self.commits = 0

    def get(self, model, user_id):
        return self.user if user_id == self.user.id else None

    def scalar(self, statement):
        return self.user

    def scalars(self, statement):
        columns = statement.column_descriptions

        if (
            len(columns) == 1
            and columns[0]["name"] == "provider"
        ):
            return FakeResult([
                identity.provider for identity in self.identities
            ])

        return FakeResult(self.identities)
    def delete(self, record):
        self.deleted.append(record)

    def commit(self):
        self.commits += 1


def make_user(password_hash=None):
    return SimpleNamespace(
        id=75,
        email="test@example.com",
        role="user",
        password_hash=password_hash,
        suspended_at=None,
        session_version=2,
    )


def make_request(token="test-session", session=None):
    headers = (
        [(b"cookie", f"careerforge_session={token}".encode())]
        if token else []
    )

    return Request({
        "type": "http",
        "method": "POST",
        "path": "/api/auth/oauth/link/disconnect",
        "headers": headers,
        "session": session if session is not None else {},
    })


def disconnect(db, provider, password=None, request=None):
    return oauth.disconnect_account(
        payload=oauth.AccountLinkRequest(
            provider=provider,
            password=password,
        ),
        request=request or make_request(),
        response=Response(),
        user_id=db.user.id,
        db=db,
    )


def test_last_oauth_method_cannot_be_disconnected():
    user = make_user()
    db = FakeDB(user, ["github"])

    with pytest.raises(HTTPException) as error:
        disconnect(db, "github")

    assert error.value.status_code == 409
    assert db.deleted == []
    assert db.commits == 0
    assert user.session_version == 2


def test_unlinked_provider_cannot_be_disconnected():
    db = FakeDB(make_user(), ["github"])

    with pytest.raises(HTTPException) as error:
        disconnect(db, "google")

    assert error.value.status_code == 404
    assert db.commits == 0


def test_two_oauth_methods_allow_disconnection(monkeypatch):
    monkeypatch.setattr(
        oauth,
        "confirm_account_ownership",
        lambda request, user, password: None,
    )

    user = make_user()
    db = FakeDB(user, ["google", "github"])
    session = {"temporary": "value"}
    request = make_request(session=session)
    response = Response()

    result = oauth.disconnect_account(
        payload=oauth.AccountLinkRequest(provider="google"),
        request=request,
        response=response,
        user_id=user.id,
        db=db,
    )

    assert result["disconnected"] == "google"
    assert result["signed_out"] is True
    assert len(db.deleted) == 1
    assert db.deleted[0].provider == "google"
    assert db.commits == 1
    assert user.session_version == 3
    assert session == {}

    cookies = response.headers.getlist("set-cookie")
    assert any("careerforge_session=" in cookie for cookie in cookies)
    assert any("csrf_token=" in cookie for cookie in cookies)


def test_password_account_can_remove_only_oauth_method(monkeypatch):
    monkeypatch.setattr(
        oauth,
        "confirm_account_ownership",
        lambda request, user, password: None,
    )

    db = FakeDB(make_user(password_hash="stored-hash"), ["google"])

    result = disconnect(db, "google", password="confirmed")

    assert result["disconnected"] == "google"
    assert db.commits == 1


def test_password_account_can_remove_only_oauth_method(monkeypatch):
    monkeypatch.setattr(
        oauth,
        "verify_password",
        lambda password, stored: (
            password == "confirmed" and stored == "stored-hash"
        ),
    )

    db = FakeDB(make_user(password_hash="stored-hash"), ["google"])
    result = disconnect(db, "google", password="confirmed")

    assert result["disconnected"] == "google"
    assert db.commits == 1

def test_suspended_account_cannot_disconnect():
    user = make_user()
    user.suspended_at = "suspended"
    db = FakeDB(user, ["google", "github"])

    with pytest.raises(HTTPException) as error:
        disconnect(db, "github")

    assert error.value.status_code == 403
    assert db.deleted == []


def test_connection_status_matches_database():
    user = make_user()
    db = FakeDB(user, ["github"])

    result = oauth.connected_account_status(
        user_id=user.id,
        db=db,
    )

    assert result == {
        "google": False,
        "github": True,
        "has_password": False,
    }


def test_link_proof_accepts_matching_session():
    token = "test-session"
    now = int(time.time())

    proof = {
        "user_id": 75,
        "provider": "google",
        "issued_at": now,
        "session_fingerprint": hashlib.sha256(
            token.encode()
        ).hexdigest(),
    }

    request = make_request(token=token)

    assert oauth.valid_account_link_proof(
        request, proof, 75, "google"
    )


def test_link_proof_rejects_wrong_identity_or_provider():
    token = "test-session"

    proof = {
        "user_id": 75,
        "provider": "google",
        "issued_at": int(time.time()),
        "session_fingerprint": hashlib.sha256(
            token.encode()
        ).hexdigest(),
    }

    request = make_request(token=token)

    assert not oauth.valid_account_link_proof(
        request, proof, 76, "google"
    )

    assert not oauth.valid_account_link_proof(
        request, proof, 75, "github"
    )

    assert not oauth.valid_account_link_proof(
        make_request("different-session"), proof, 75, "google"
    )


def test_expired_link_proof_is_rejected():
    token = "test-session"

    proof = {
        "user_id": 75,
        "provider": "github",
        "issued_at": int(time.time()) - 301,
        "session_fingerprint": hashlib.sha256(
            token.encode()
        ).hexdigest(),
    }

    assert not oauth.valid_account_link_proof(
        make_request(token), proof, 75, "github"
    )

def test_failed_ownership_confirmation_blocks_disconnection(monkeypatch):
    def reject(request, user, password):
        raise HTTPException(
            status_code=401,
            detail="Invalid confirmation.",
        )

    monkeypatch.setattr(
        oauth,
        "confirm_account_ownership",
        reject,
    )

    db = FakeDB(make_user(), ["google", "github"])

    with pytest.raises(HTTPException) as error:
        disconnect(db, "google")

    assert error.value.status_code == 401
    assert db.deleted == []
    assert db.commits == 0