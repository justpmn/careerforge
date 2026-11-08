
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from src.backend.app.api.routes.auth import router as auth_router
from src.backend.app.api.routes.ai_mentor import router as mentor_router
from src.backend.app.core.config import settings
from src.backend.app.core.security import verify_password
from src.backend.app.core.tokens import decode_access_token
from src.backend.app.database.models.user import User
from src.backend.app.database.session import engine, get_db


TEST_PASSWORD = "CareerForge-Secure-Test-2026!"


@pytest.fixture
def api_context(monkeypatch):
    
    if engine.url.database != "careerforge_test":
        raise RuntimeError(
            "Authentication API tests require careerforge_test."
        )

    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "careerforge-test-signing-secret-" + "a" * 48,
    )

    app = FastAPI()
    app.include_router(auth_router, prefix="/api")
    app.include_router(mentor_router, prefix="/api/ai-mentor")

    with engine.connect() as connection:
        transaction = connection.begin()

        def test_db():
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as db:
                yield db

        app.dependency_overrides[get_db] = test_db

        try:
            with TestClient(app) as client:
                yield client, connection
        finally:
            transaction.rollback()


def unique_email():
    return f"careerforge-pytest-{uuid4().hex}@example.com"


def register_account(client, email=None):
    email = email or unique_email()

    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "CareerForge Test User",
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    return response

def verify_registered_user(connection, registration):
    user_id = registration.json()["id"]

    connection.execute(
        update(User)
        .where(User.id == user_id)
        .values(email_verified_at=datetime.now(timezone.utc))
    )

def test_registration_creates_secure_user(api_context):
    client, connection = api_context

    response = register_account(client)

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["full_name"] == "CareerForge Test User"
    assert "password" not in data
    assert "password_hash" not in data

    user = connection.execute(
        select(
            User.email,
            User.password_hash,
            User.role,
        ).where(User.id == data["id"])
    ).one()

    assert user.role == "user"
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password(TEST_PASSWORD, user.password_hash)


def test_duplicate_registration_rejected(api_context):
    client, _ = api_context

    email = unique_email()

    first = register_account(client, email)
    second = register_account(client, email.upper())

    assert first.status_code == 201
    assert second.status_code == 409


def test_registration_rejects_admin_role(api_context):
    client, _ = api_context

    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Unauthorized Admin",
            "email": unique_email(),
            "password": TEST_PASSWORD,
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_login_returns_valid_jwt(api_context):
    client, connection = api_context

    email = unique_email()
    registration = register_account(client, email)

    assert registration.status_code == 201
    verify_registered_user(connection, registration)

    login = client.post(
        "/api/auth/login",
        json={
            "email": email.upper(),
            "password": TEST_PASSWORD,
        },
    )

    assert login.status_code == 200, login.text

    token_data = login.json()

    assert token_data["token_type"] == "bearer"
    assert decode_access_token(
        token_data["access_token"]
    ) == registration.json()["id"]


def test_login_rejects_invalid_credentials(api_context):
    client, _ = api_context

    email = unique_email()
    registration = register_account(client, email)

    assert registration.status_code == 201

    wrong_password = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "IncorrectPassword123!",
        },
    )

    unknown_user = client.post(
        "/api/auth/login",
        json={
            "email": unique_email(),
            "password": TEST_PASSWORD,
        },
    )

    assert wrong_password.status_code == 401
    assert unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json()


def test_authenticated_mentor_access(api_context):
    client, connection = api_context

    registration = register_account(client)

    assert registration.status_code == 201
    verify_registered_user(connection, registration)
    
    endpoint = "/api/ai-mentor/chat/assessment/persistent"
    
    payload = {
            "message": "Which competencies should I assess?",
            "career_key": "data_scientist",
        }
    
    unauthorized = client.post(
            endpoint,
            json=payload,
        )
    
    assert unauthorized.status_code == 401

    email = registration.json()["email"]
    user_id = registration.json()["id"]

    login = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    

    with patch(
        "src.backend.app.api.routes.ai_mentor.generate_persistent_assessment_mentor_response",
        new_callable=AsyncMock,
    ) as mock_mentor:

        mock_mentor.return_value = {
            "conversation_id": 42,
            "response": "Start with statistics.",
        }

        authorized = client.post(
            endpoint,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert authorized.status_code == 200, authorized.text
        assert mock_mentor.await_args.kwargs["user_id"] == user_id
