
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.backend.app.api.routes.ai_mentor import router
from src.backend.app.core.config import settings
from src.backend.app.core.security import hash_password
from src.backend.app.core.tokens import create_access_token
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.mentor import (
    MentorConversation,
    MentorMessage,
)
from src.backend.app.database.models.user import User
from src.backend.app.database.session import engine, get_db
from src.backend.app.services.llm_service import LLMServiceError


@pytest.fixture
def conversation_api(monkeypatch):
    monkeypatch.setattr(
        settings,
        "jwt_secret_key",
        "careerforge-conversation-test-secret-" + "a" * 48,
    )

    app = FastAPI()
    app.include_router(router, prefix="/api/ai-mentor")

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
            with Session(
                bind=connection,
                join_transaction_mode="create_savepoint",
            ) as db:
                suffix = uuid4().hex
                password_hash = hash_password(
                    "CareerForge-Test-Password-2026!"
                )

                user_a = User(
                    full_name="Conversation Test User A",
                    email=f"mentor-a-{suffix}@example.com",
                    password_hash=password_hash,
                    role="user",
                )

                user_b = User(
                    full_name="Conversation Test User B",
                    email=f"mentor-b-{suffix}@example.com",
                    password_hash=password_hash,
                    role="user",
                )

                career_a = Career(
                    career_key=f"pytest_data_scientist_{suffix}",
                    name=f"Pytest Data Scientist {suffix}",
                )

                career_b = Career(
                    career_key=f"pytest_backend_developer_{suffix}",
                    name=f"Pytest Backend Developer {suffix}",
                )

                db.add_all([
                    user_a,
                    user_b,
                    career_a,
                    career_b,
                ])

                db.flush()

                data = {
                    "user_a": user_a.id,
                    "user_b": user_b.id,
                    "career_a": career_a.career_key,
                    "career_b": career_b.career_key,
                    "career_a_id": career_a.id,
                }

                db.commit()

            with TestClient(app) as client:
                yield client, connection, data

        finally:
            transaction.rollback()


@pytest.fixture
def mock_mentor_generation():
    with (
        patch(
            "src.backend.app.services.assessment_mentor_service.analyze_competency_gaps",
            return_value={"career_name": "Test Data Scientist"},
        ),
        patch(
            "src.backend.app.services.assessment_mentor_service.build_mentor_context",
            return_value={"source": "test_assessment"},
        ),
        patch(
            "src.backend.app.services.assessment_mentor_service.generate_mentor_response",
            new_callable=AsyncMock,
        ) as mock_llm,
    ):
        mock_llm.return_value = "Start with statistics."
        yield mock_llm


def auth_headers(user_id):
    return {
        "Authorization": f"Bearer {create_access_token(user_id)}"
    }


def send_question(
    client,
    user_id,
    career_key,
    message,
    conversation_id=None,
):
    payload = {
        "message": message,
        "career_key": career_key,
    }

    if conversation_id is not None:
        payload["conversation_id"] = conversation_id

    return client.post(
        "/api/ai-mentor/chat/assessment/persistent",
        json=payload,
        headers=auth_headers(user_id),
    )


def test_persistent_conversation_history(
    conversation_api,
    mock_mentor_generation,
):
    client, connection, data = conversation_api

    first = send_question(
        client,
        data["user_a"],
        data["career_a"],
        "Which competencies should I assess?",
    )

    assert first.status_code == 200, first.text

    conversation_id = first.json()["conversation_id"]

    second = send_question(
        client,
        data["user_a"],
        data["career_a"],
        "Which should I assess first?",
        conversation_id,
    )

    assert second.status_code == 200, second.text
    assert second.json()["conversation_id"] == conversation_id

    assert mock_mentor_generation.await_count == 2

    previous_history = (
        mock_mentor_generation.await_args_list[1]
        .kwargs["history"]
    )

    assert previous_history == [
        {
            "role": "user",
            "content": "Which competencies should I assess?",
        },
        {
            "role": "assistant",
            "content": "Start with statistics.",
        },
    ]

    response = client.get(
        f"/api/ai-mentor/conversations/{conversation_id}/messages",
        headers=auth_headers(data["user_a"]),
    )

    assert response.status_code == 200, response.text
    assert len(response.json()) == 4

    stored_roles = connection.execute(
        select(MentorMessage.role)
        .where(MentorMessage.conversation_id == conversation_id)
        .order_by(MentorMessage.id)
    ).scalars().all()

    assert stored_roles == [
        "user",
        "mentor",
        "user",
        "mentor",
    ]


def test_conversation_user_isolation(
    conversation_api,
    mock_mentor_generation,
):
    client, connection, data = conversation_api

    first = send_question(
        client,
        data["user_a"],
        data["career_a"],
        "My first conversation",
    )

    second = send_question(
        client,
        data["user_b"],
        data["career_a"],
        "My private conversation",
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    first_id = first.json()["conversation_id"]
    second_id = second.json()["conversation_id"]

    listing = client.get(
        "/api/ai-mentor/conversations",
        headers=auth_headers(data["user_a"]),
    )

    assert listing.status_code == 200

    conversation_ids = {
        item["id"] for item in listing.json()
    }

    assert first_id in conversation_ids
    assert second_id not in conversation_ids

    forbidden = client.get(
        f"/api/ai-mentor/conversations/{second_id}/messages",
        headers=auth_headers(data["user_a"]),
    )

    assert forbidden.status_code == 404


def test_career_mismatch_rejected(
    conversation_api,
    mock_mentor_generation,
):
    client, connection, data = conversation_api

    first = send_question(
        client,
        data["user_a"],
        data["career_a"],
        "Assess my data science skills.",
    )

    assert first.status_code == 200

    conversation_id = first.json()["conversation_id"]

    mismatch = send_question(
        client,
        data["user_a"],
        data["career_b"],
        "Switch to backend development.",
        conversation_id,
    )

    assert mismatch.status_code == 404
    assert mock_mentor_generation.await_count == 1

    message_count = connection.scalar(
        select(func.count())
        .select_from(MentorMessage)
        .where(MentorMessage.conversation_id == conversation_id)
    )

    assert message_count == 2


def test_llm_failure_does_not_create_conversation(
    conversation_api,
    mock_mentor_generation,
):
    client, connection, data = conversation_api

    before = connection.scalar(
        select(func.count()).select_from(MentorConversation)
    )

    mock_mentor_generation.side_effect = LLMServiceError(
        "Ollama unavailable."
    )

    response = send_question(
        client,
        data["user_a"],
        data["career_a"],
        "Help me assess my skills.",
    )

    assert response.status_code == 503

    after = connection.scalar(
        select(func.count()).select_from(MentorConversation)
    )

    assert after == before


def test_unauthenticated_conversation_request(
    conversation_api,
):
    client, connection, data = conversation_api

    response = client.get(
        "/api/ai-mentor/conversations"
    )

    assert response.status_code == 401
