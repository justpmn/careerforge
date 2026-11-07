
"""
CareerForge administrator authorization tests.

Tests:
- Admin routes are registered
- Anonymous requests are rejected
- Ordinary users cannot access admin endpoints
- Administrators can access their identity endpoint

Uses a standalone FastAPI test app and mocked database
sessions. Does not modify production data.
"""

import unittest

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.api.routes.admin import (
    router as admin_router,
)
from src.backend.app.database.session import get_db


ADMIN_ENDPOINTS = [
    "/api/admin/me",
    "/api/admin/overview",
    "/api/admin/users",
    "/api/admin/logs",
    "/api/admin/health",
    "/api/admin/careers/cloud_engineer/resources",
]


def create_test_app() -> FastAPI:
    """
    Create an isolated app containing the real
    CareerForge admin routes and dependencies.
    """

    app = FastAPI()

    app.include_router(
        admin_router,
        prefix="/api",
    )

    return app


def make_fake_user(role: str):
    """
    Construct a test account without writing
    anything to the actual user database.
    """

    return SimpleNamespace(
        id=999,
        full_name="Test Administrator",
        name="Test Administrator",
        email="admin-test@example.invalid",
        role=role,
        onboarding_completed=True,
        created_at=datetime.now(timezone.utc),
    )


class TestAdminAuthorization(unittest.TestCase):

    def setUp(self):
        self.app = create_test_app()

        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.client.close()

    def authenticate_as(self, role: str):
        """
        Simulate an authenticated identity.

        The real require_admin dependency must still
        execute. Only authentication identity and
        database access are replaced.
        """

        fake_user = make_fake_user(role)

        fake_db = MagicMock()

        fake_db.get.return_value = fake_user
        fake_db.scalar.return_value = fake_user

        fake_db.execute.return_value.scalar_one_or_none.return_value = (
            fake_user
        )

        fake_db.execute.return_value.scalar_one.return_value = (
            fake_user
        )

        fake_db.execute.return_value.scalar.return_value = (
            fake_user
        )

        fake_db.query.return_value.filter.return_value.first.return_value = (
            fake_user
        )

        fake_db.query.return_value.filter_by.return_value.first.return_value = (
            fake_user
        )

        def override_current_user_id():
            return fake_user.id

        def override_get_db():
            yield fake_db

        self.app.dependency_overrides[
            get_current_user_id
        ] = override_current_user_id

        self.app.dependency_overrides[
            get_db
        ] = override_get_db


    
    def test_admin_routes_are_registered(self):
        """
        Verify admin routes through actual HTTP requests.

        Existing protected endpoints must return HTTP 401
        to anonymous users rather than HTTP 404.

        Also verify that an unknown endpoint returns 404.
        """

        for endpoint in ADMIN_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(
                    response.status_code,
                    401,
                    (
                        f"Expected protected endpoint "
                        f"{endpoint} to return 401, "
                        f"received {response.status_code}."
                    ),
                )

        # Negative control: a route that does not exist.
        response = self.client.get(
            "/api/admin/nonexistent-test-route"
        )

        self.assertEqual(
            response.status_code,
            404,
            "Unknown admin endpoints should return 404.",
        )


    def test_anonymous_user_cannot_access_admin_routes(self):
        """
        Unauthenticated requests should return HTTP 401.
        """

        for endpoint in ADMIN_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(
                    response.status_code,
                    401,
                    f"Anonymous access to {endpoint}: "
                    f"{response.status_code}",
                )

    def test_regular_user_cannot_access_admin_routes(self):
        """
        An authenticated user without admin privileges
        should receive HTTP 403.
        """

        self.authenticate_as("user")

        for endpoint in ADMIN_ENDPOINTS:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(
                    response.status_code,
                    403,
                    f"Regular user access to {endpoint}: "
                    f"{response.status_code}",
                )

    def test_administrator_can_access_identity(self):
        """
        Verify that the real admin guard allows a
        user with the administrator role.
        """

        self.authenticate_as("admin")

        response = self.client.get(
            "/api/admin/me"
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        data = response.json()

        self.assertEqual(
            data["role"],
            "admin",
        )


if __name__ == "__main__":
    unittest.main()
