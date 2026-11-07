
import unittest

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db

from src.backend.app.api.routes.learning_roadmaps import (
    router as roadmap_router,
)

from src.backend.app.api.routes.skill_gaps import (
    router as skill_gap_router,
)


USER_A = 101
USER_B = 202
CAREER = "data_engineer"

ROADMAP_URL = (
    f"/api/roadmaps/users/{{user_id}}/careers/{CAREER}"
)

SKILL_GAP_URL = (
    f"/api/skill-gaps/users/{{user_id}}/careers/{CAREER}"
)

ROADMAP_SERVICE = (
    "src.backend.app.api.routes.learning_roadmaps."
    "generate_learning_roadmap"
)

SKILL_GAP_SERVICE = (
    "src.backend.app.api.routes.skill_gaps."
    "analyze_competency_gaps"
)


class TestRoadmapGapOwnership(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()

        self.app.include_router(
            roadmap_router,
            prefix="/api",
        )

        self.app.include_router(
            skill_gap_router,
            prefix="/api",
        )

        self.db = MagicMock()

        self.app.dependency_overrides[get_db] = (
            lambda: self.db
        )

        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.client.close()

    def authenticate(self, user_id: int):
        self.app.dependency_overrides[
            get_current_user_id
        ] = lambda: user_id

    def test_anonymous_requests_are_rejected(self):
        for url in [ROADMAP_URL, SKILL_GAP_URL]:
            with self.subTest(url=url):
                response = self.client.get(
                    url.format(user_id=USER_A)
                )

                self.assertEqual(
                    response.status_code,
                    401,
                    response.text,
                )

    def test_cross_user_requests_are_forbidden(self):
        self.authenticate(USER_A)

        for url, service_path in [
            (ROADMAP_URL, ROADMAP_SERVICE),
            (SKILL_GAP_URL, SKILL_GAP_SERVICE),
        ]:
            with self.subTest(url=url):
                with patch(service_path) as service:
                    response = self.client.get(
                        url.format(user_id=USER_B)
                    )

                    self.assertEqual(
                        response.status_code,
                        403,
                        response.text,
                    )

                    service.assert_not_called()

    def test_owner_can_access_roadmap(self):
        self.authenticate(USER_A)

        with patch(
            ROADMAP_SERVICE,
            return_value={"status": "ok"},
        ) as service:
            response = self.client.get(
                ROADMAP_URL.format(user_id=USER_A)
            )

            self.assertEqual(
                response.status_code,
                200,
                response.text,
            )

            service.assert_called_once_with(
                db=self.db,
                user_id=USER_A,
                career_key=CAREER,
                focus_competencies=None,
                optional_competencies=None,
            )

    def test_owner_can_access_skill_gaps(self):
        self.authenticate(USER_A)

        with patch(
            SKILL_GAP_SERVICE,
            return_value={"status": "ok"},
        ) as service:
            response = self.client.get(
                SKILL_GAP_URL.format(user_id=USER_A)
            )

            self.assertEqual(
                response.status_code,
                200,
                response.text,
            )

            service.assert_called_once_with(
                db=self.db,
                user_id=USER_A,
                career_key=CAREER,
            )

    def test_roadmap_personalization_is_preserved(self):
        self.authenticate(USER_A)

        with patch(
            ROADMAP_SERVICE,
            return_value={"status": "ok"},
        ) as service:
            response = self.client.get(
                ROADMAP_URL.format(user_id=USER_A),
                params=[
                    ("focus_competencies", "sql"),
                    ("optional_competencies", "ci_cd"),
                ],
            )

            self.assertEqual(
                response.status_code,
                200,
                response.text,
            )

            service.assert_called_once_with(
                db=self.db,
                user_id=USER_A,
                career_key=CAREER,
                focus_competencies=["sql"],
                optional_competencies=["ci_cd"],
            )


if __name__ == "__main__":
    unittest.main()
