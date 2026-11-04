
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user_skill import UserSkill
from src.backend.app.database.models.user_learning_progress import (
    UserLearningProgress,
)

from src.backend.app.api.routes.learning_progress import (
    router as progress_router,
)
from src.backend.app.api.routes.skill_evidence import (
    router as skills_router,
)
from src.backend.app.api.routes.ai_mentor import (
    router as mentor_router,
)


USER_A = 101
USER_B = 202

PROGRESS_MODULE = (
    "src.backend.app.api.routes.learning_progress"
)
MENTOR_MODULE = (
    "src.backend.app.api.routes.ai_mentor"
)


class TestRemainingOwnership(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()

        self.app.include_router(
            progress_router,
            prefix="/api",
        )
        self.app.include_router(
            skills_router,
            prefix="/api",
        )
        self.app.include_router(
            mentor_router,
            prefix="/api/ai-mentor",
        )

        self.db = MagicMock()

        self.app.dependency_overrides[get_db] = (
            lambda: self.db
        )

        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.client.close()

    def authenticate(self, user_id):
        self.app.dependency_overrides[
            get_current_user_id
        ] = lambda: user_id

    def test_anonymous_protected_routes(self):
        endpoints = [
            "/api/roadmaps/learning-progress/data_scientist",
            "/api/roadmaps/manual-skills",
            "/api/ai-mentor/conversations",
            "/api/ai-mentor/conversations/999/messages",
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(
                    response.status_code,
                    401,
                    response.text,
                )

    def test_learning_progress_read_filters_user(self):
        self.authenticate(USER_A)

        self.db.scalars.return_value.all.return_value = []

        with patch(
            f"{PROGRESS_MODULE}.get_career_and_keys",
            return_value=(
                SimpleNamespace(id=77),
                {"python"},
            ),
        ):
            response = self.client.get(
                "/api/roadmaps/learning-progress/data_scientist",
                params={"user_id": USER_B},
            )

        self.assertEqual(response.status_code, 200)

        statement = self.db.scalars.call_args.args[0]
        parameters = list(statement.compile().params.values())

        self.assertIn(USER_A, parameters)
        self.assertIn(77, parameters)
        self.assertNotIn(USER_B, parameters)

    def test_learning_progress_write_uses_owner(self):
        self.authenticate(USER_A)
        self.db.get.return_value = None

        with patch(
            f"{PROGRESS_MODULE}.get_career_and_keys",
            return_value=(
                SimpleNamespace(id=77),
                {"python"},
            ),
        ):
            response = self.client.put(
                "/api/roadmaps/learning-progress/"
                "data_scientist/python",
                params={"user_id": USER_B},
                json={"learned": True},
            )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        self.db.get.assert_called_once_with(
            UserLearningProgress,
            (USER_A, 77, "python"),
        )

        record = self.db.add.call_args.args[0]

        self.assertEqual(record.user_id, USER_A)
        self.assertTrue(record.learned)
        self.db.commit.assert_called_once()

    def test_manual_skill_read_filters_user(self):
        self.authenticate(USER_A)

        self.db.scalars.return_value.all.return_value = []

        response = self.client.get(
            "/api/roadmaps/manual-skills",
            params={"user_id": USER_B},
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        statement = self.db.scalars.call_args.args[0]
        parameters = list(statement.compile().params.values())

        self.assertIn(USER_A, parameters)
        self.assertIn("manual", parameters)
        self.assertNotIn(USER_B, parameters)

    def test_manual_skill_creation_uses_owner(self):
        self.authenticate(USER_A)

        skill = SimpleNamespace(
            id=3,
            name="Python",
            category="Programming",
        )

        def fake_get(model, key):
            if model is Skill and key == 3:
                return skill

            if model is UserSkill:
                return None

            return None

        self.db.get.side_effect = fake_get

        response = self.client.post(
            "/api/roadmaps/manual-skills",
            json={
                "skill_id": 3,
                "user_id": USER_B,
            },
        )

        self.assertEqual(
            response.status_code,
            201,
            response.text,
        )

        record = self.db.add.call_args.args[0]

        self.assertEqual(record.user_id, USER_A)
        self.assertEqual(record.skill_id, 3)
        self.assertEqual(record.source, "manual")

        self.db.commit.assert_called_once()

    def test_manual_skill_removal_uses_owner(self):
        self.authenticate(USER_A)

        # Simulate a skill not belonging to User A.
        self.db.get.return_value = None

        response = self.client.delete(
            "/api/roadmaps/manual-skills/3",
        )

        self.assertEqual(
            response.status_code,
            404,
            response.text,
        )

        self.db.get.assert_called_once_with(
            UserSkill,
            (USER_A, 3),
        )

        self.db.delete.assert_not_called()

    def test_mentor_list_uses_authenticated_user(self):
        self.authenticate(USER_A)

        with patch(
            f"{MENTOR_MODULE}.list_owned_mentor_conversations",
            return_value=[],
        ) as service:
            response = self.client.get(
                "/api/ai-mentor/conversations",
                params={"user_id": USER_B},
            )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        service.assert_called_once_with(
            db=self.db,
            user_id=USER_A,
        )

    def test_foreign_mentor_conversation_rejected(self):
        self.authenticate(USER_A)

        with patch(
            f"{MENTOR_MODULE}.list_owned_mentor_messages",
            side_effect=ValueError(
                "Conversation not found."
            ),
        ) as service:
            response = self.client.get(
                "/api/ai-mentor/conversations/999/messages",
            )

        self.assertEqual(
            response.status_code,
            404,
            response.text,
        )

        service.assert_called_once_with(
            db=self.db,
            user_id=USER_A,
            conversation_id=999,
        )

    def test_persistent_chat_forwards_authenticated_user(self):
        self.authenticate(USER_A)

        self.db.get.return_value = SimpleNamespace(
            id=USER_A,
            target_career_id=None,
        )

        with (
            patch(
                f"{MENTOR_MODULE}.resolve_explicit_career_change",
                return_value=None,
            ),
            patch(
                f"{MENTOR_MODULE}."
                "generate_persistent_assessment_mentor_response",
                new_callable=AsyncMock,
            ) as service,
        ):
            service.return_value = {
                "conversation_id": 999,
                "response": "Mocked advice",
            }

            response = self.client.post(
                "/api/ai-mentor/chat/assessment/persistent",
                json={
                    "message": "Help me learn Python",
                    "career_key": "data_engineer",
                    "conversation_id": 999,
                },
            )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        service.assert_awaited_once_with(
            db=self.db,
            user_id=USER_A,
            career_key="data_engineer",
            message="Help me learn Python",
            conversation_id=999,
        )
        
    def test_anonymous_cannot_use_basic_chat(self):
        with patch(
            f"{MENTOR_MODULE}.generate_mentor_response",
            new_callable=AsyncMock,
        ) as llm:
            response = self.client.post(
                "/api/ai-mentor/chat",
                json={"message": "Hello"},
            )

        self.assertEqual(
            response.status_code,
            401,
            response.text,
        )
        llm.assert_not_awaited()

    def test_authenticated_user_can_use_basic_chat(self):
        self.authenticate(USER_A)

        with patch(
            f"{MENTOR_MODULE}.generate_mentor_response",
            new_callable=AsyncMock,
            return_value="Mocked mentoring response",
        ) as llm:
            response = self.client.post(
                "/api/ai-mentor/chat",
                json={"message": "Hello"},
            )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )
        self.assertEqual(
            response.json()["response"],
            "Mocked mentoring response",
        )
        llm.assert_awaited_once()



if __name__ == "__main__":
    unittest.main()
