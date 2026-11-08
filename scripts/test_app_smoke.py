
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.backend.app.main import app


class TestCareerForgeAppSmoke(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Use the real FastAPI application.
        # Do not start background lifecycle tasks.
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_protected_user_endpoints(self):
        endpoints = [
            "/api/auth/me",
            "/api/roadmaps/manual-skills",
            "/api/roadmaps/skill-evidence/me",
            "/api/roadmaps/learning-progress/data_scientist",
            "/api/ai-mentor/conversations",
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(
                    response.status_code,
                    401,
                    (
                        f"{endpoint}: expected 401, "
                        f"received {response.status_code}"
                    ),
                )

    def test_admin_endpoint_is_protected(self):
        response = self.client.get(
            "/api/admin/me"
        )

        self.assertEqual(
            response.status_code,
            401,
            response.text,
        )

    def test_roadmap_and_skill_gap_endpoints(self):
        endpoints = [
            "/api/roadmaps/users/101/careers/data_engineer",
            "/api/skill-gaps/users/101/careers/data_engineer",
        ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(
                    response.status_code,
                    401,
                    response.text,
                )

    def test_mentor_chat_rejects_anonymous_user(self):
        with patch(
            "src.backend.app.api.routes.ai_mentor."
            "generate_mentor_response",
            new_callable=AsyncMock,
        ) as llm:
            response = self.client.post(
                "/api/ai-mentor/chat",
                json={
                    "message": "Help me learn Python."
                },
            )

        self.assertEqual(
            response.status_code,
            401,
            response.text,
        )

        llm.assert_not_awaited()

    def test_login_request_validation(self):
        response = self.client.post(
            "/api/auth/login",
            json={},
        )

        self.assertEqual(
            response.status_code,
            422,
            response.text,
        )

    def test_registration_request_validation(self):
        response = self.client.post(
            "/api/auth/register",
            json={},
        )

        self.assertEqual(
            response.status_code,
            422,
            response.text,
        )


if __name__ == "__main__":
    unittest.main()
