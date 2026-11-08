
"""
CareerForge user data ownership tests.

Tests protected CV and competency assessment endpoints.

Uses:
- Actual FastAPI routers
- Mock authentication identities
- Mock database sessions
- Mock competency services

Does not write to the real PostgreSQL database.
"""

import unittest

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.app.api.auth import get_current_user_id

from src.backend.app.database.session import get_db

from src.backend.app.api.routes.recommendations import (
    router as recommendations_router,
)

from src.backend.app.api.routes.competency_assessment import (
    router as competency_router,
)


USER_A = 101
USER_B = 202
CAREER = "data_engineer"


class TestUserDataOwnership(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()

        self.app.include_router(
            recommendations_router,
            prefix="/api",
        )

        self.app.include_router(
            competency_router,
            prefix="/api",
        )

        self.mock_db = MagicMock()

        def override_get_db():
            yield self.mock_db

        self.app.dependency_overrides[
            get_db
        ] = override_get_db

        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.client.close()

    def authenticate(self, user_id: int):
        """
        Simulate a validated login identity.
        """

        def override_current_user():
            return user_id

        self.app.dependency_overrides[
            get_current_user_id
        ] = override_current_user

    def test_anonymous_cannot_access_latest_cv(self):
        response = self.client.get(
            "/api/recommendations/resumes/latest"
        )

        self.assertEqual(
            response.status_code,
            401,
            response.text,
        )

    def test_anonymous_cannot_access_assessments(self):
        response = self.client.get(
            f"/api/roadmaps/competency-assessments/{CAREER}"
        )

        self.assertEqual(
            response.status_code,
            401,
            response.text,
        )

    def test_user_cannot_upload_cv_for_another_user(self):
        """
        User A attempts to upload a CV for User B.

        Must return 403 before text extraction or
        recommendation processing takes place.
        """

        self.authenticate(USER_A)

        with (
            patch(
                "src.backend.app.api.routes.recommendations.extract_resume_text"
            ) as extract_mock,
            patch(
                "src.backend.app.api.routes.recommendations.save_resume_analysis"
            ) as save_mock,
        ):
            response = self.client.post(
                "/api/recommendations/upload",
                data={
                    "user_id": str(USER_B),
                    "top_k": "3",
                },
                files={
                    "file": (
                        "sample.pdf",
                        b"%PDF-1.4\nTest document",
                        "application/pdf",
                    ),
                },
            )

            self.assertEqual(
                response.status_code,
                403,
                response.text,
            )

            extract_mock.assert_not_called()
            save_mock.assert_not_called()

    def test_assessment_read_uses_authenticated_user(self):
        """
        Ensure competency assessment reads receive
        the authenticated user's ID.
        """

        self.authenticate(USER_A)

        with patch(
            "src.backend.app.api.routes.competency_assessment.list_assessments",
            return_value=[],
        ) as list_mock:

            response = self.client.get(
                f"/api/roadmaps/competency-assessments/{CAREER}",
                params={"user_id": USER_B},
            )

            self.assertEqual(
                response.status_code,
                200,
                response.text,
            )

            list_mock.assert_called_once_with(
                self.mock_db,
                USER_A,
                CAREER,
            )

    def test_assessment_update_uses_authenticated_user(self):
        """
        Ensure updates are attributed to the
        authenticated user, not another account.
        """

        self.authenticate(USER_A)

        now = datetime.now(timezone.utc)

        fake_record = SimpleNamespace(
            competency_key="sql",
            proficiency_level="intermediate",
            notes="Practicing SQL queries",
            created_at=now,
            updated_at=now,
        )

        with patch(
            "src.backend.app.api.routes.competency_assessment.save_assessment",
            return_value=fake_record,
        ) as save_mock:

            response = self.client.put(
                f"/api/roadmaps/competency-assessments/{CAREER}/sql",
                json={
                    "proficiency_level": "intermediate",
                    "notes": "Practicing SQL queries",
                    "user_id": USER_B,
                },
            )

            self.assertEqual(
                response.status_code,
                200,
                response.text,
            )

            self.assertEqual(
                response.json()["proficiency_level"],
                "intermediate",
            )

            save_mock.assert_called_once_with(
                db=self.mock_db,
                user_id=USER_A,
                career_key=CAREER,
                competency_key="sql",
                proficiency_level="intermediate",
                notes="Practicing SQL queries",
            )

    def test_different_users_have_separate_assessment_contexts(self):
        """
        Ensure each request passes its own authenticated
        identity to the assessment service.
        """

        with patch(
            "src.backend.app.api.routes.competency_assessment.list_assessments",
            return_value=[],
        ) as list_mock:

            self.authenticate(USER_A)

            first = self.client.get(
                f"/api/roadmaps/competency-assessments/{CAREER}"
            )

            self.authenticate(USER_B)

            second = self.client.get(
                f"/api/roadmaps/competency-assessments/{CAREER}"
            )

            self.assertEqual(first.status_code, 200)
            self.assertEqual(second.status_code, 200)

            self.assertEqual(
                list_mock.call_args_list,
                [
                    call(self.mock_db, USER_A, CAREER),
                    call(self.mock_db, USER_B, CAREER),
                ],
            )


if __name__ == "__main__":
    unittest.main()
