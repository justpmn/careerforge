
import unittest

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.backend.app.api.auth import (
    create_csrf_token,
    get_current_user_id,
)
from src.backend.app.api.routes.auth import (
    router as auth_router,
)
from src.backend.app.database.session import get_db


USER_ID = 101
TEST_SECRET = "careerforge-session-test-secret"


class TestSessionSecurity(unittest.TestCase):

    def setUp(self):
        self.app = FastAPI()

        self.app.include_router(
            auth_router,
            prefix="/api",
        )

        @self.app.get("/api/test-session/read")
        def protected_read(
            user_id: int = Depends(get_current_user_id),
        ):
            return {"user_id": user_id}

        @self.app.post("/api/test-session/write")
        def protected_write(
            user_id: int = Depends(get_current_user_id),
        ):
            return {"user_id": user_id}

        self.db = MagicMock()

        self.user = SimpleNamespace(
            id=USER_ID,
            full_name="Session Test User",
            email="session-test@example.com",
            password_hash="test-password-hash",
            onboarding_completed=False,
        )

        self.db.get.return_value = self.user
        self.db.scalar.return_value = self.user

        self.app.dependency_overrides[get_db] = (
            lambda: self.db
        )

        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.client.close()

    def set_session_cookies(
        self,
        session_token="test-session-token",
        csrf_token=None,
    ):
        self.client.cookies.set(
            "careerforge_session",
            session_token,
            path="/api",
        )

        if csrf_token is not None:
            self.client.cookies.set(
                "csrf_token",
                csrf_token,
                path="/",
            )

    def signed_csrf(self, session_token):
        with patch(
            "src.backend.app.api.auth.get_jwt_secret",
            return_value=TEST_SECRET,
        ):
            return create_csrf_token(session_token)

    def test_anonymous_request_is_rejected(self):
        response = self.client.get(
            "/api/test-session/read"
        )

        self.assertEqual(response.status_code, 401)

    def test_invalid_bearer_token_is_rejected(self):
        with patch(
            "src.backend.app.api.auth.decode_access_token",
            side_effect=ValueError("Invalid token"),
        ):
            response = self.client.get(
                "/api/test-session/read",
                headers={
                    "Authorization": "Bearer invalid-token"
                },
            )

        self.assertEqual(response.status_code, 401)

    def test_decoder_expiration_error_is_rejected(self):
        # Tests authentication's handling of an expiration
        # error, not the JWT decoder's expiration logic.
        with patch(
            "src.backend.app.api.auth.decode_access_token",
            side_effect=ValueError("Token expired"),
        ):
            response = self.client.get(
                "/api/test-session/read",
                headers={
                    "Authorization": "Bearer expired-token"
                },
            )

        self.assertEqual(response.status_code, 401)

    def test_deleted_user_token_is_rejected(self):
        self.db.get.return_value = None

        with patch(
            "src.backend.app.api.auth.decode_access_token",
            return_value=USER_ID,
        ):
            response = self.client.get(
                "/api/test-session/read",
                headers={
                    "Authorization": "Bearer test-token"
                },
            )

        self.assertEqual(response.status_code, 401)

    def test_valid_cookie_allows_read(self):
        self.set_session_cookies()

        with patch(
            "src.backend.app.api.auth.decode_access_token",
            return_value=USER_ID,
        ):
            response = self.client.get(
                "/api/test-session/read"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["user_id"],
            USER_ID,
        )

    def test_cookie_write_requires_csrf(self):
        self.set_session_cookies()

        with patch(
            "src.backend.app.api.auth.decode_access_token",
            return_value=USER_ID,
        ):
            response = self.client.post(
                "/api/test-session/write"
            )

        self.assertEqual(response.status_code, 403)

    def test_cookie_write_rejects_mismatched_csrf(self):
        token = "test-session-token"
        csrf = self.signed_csrf(token)

        self.set_session_cookies(
            session_token=token,
            csrf_token=csrf,
        )

        with patch(
            "src.backend.app.api.auth.decode_access_token",
            return_value=USER_ID,
        ):
            response = self.client.post(
                "/api/test-session/write",
                headers={"X-CSRF-Token": "incorrect-token"},
            )

        self.assertEqual(response.status_code, 403)

    def test_csrf_cannot_be_reused_for_another_session(self):
        token_a = "session-a"
        token_b = "session-b"

        csrf_from_a = self.signed_csrf(token_a)

        self.set_session_cookies(
            session_token=token_b,
            csrf_token=csrf_from_a,
        )

        with (
            patch(
                "src.backend.app.api.auth.decode_access_token",
                return_value=USER_ID,
            ),
            patch(
                "src.backend.app.api.auth.get_jwt_secret",
                return_value=TEST_SECRET,
            ),
        ):
            response = self.client.post(
                "/api/test-session/write",
                headers={"X-CSRF-Token": csrf_from_a},
            )

        self.assertEqual(response.status_code, 403)

    def test_valid_csrf_allows_cookie_write(self):
        token = "test-session-token"
        csrf = self.signed_csrf(token)

        self.set_session_cookies(
            session_token=token,
            csrf_token=csrf,
        )

        with (
            patch(
                "src.backend.app.api.auth.decode_access_token",
                return_value=USER_ID,
            ),
            patch(
                "src.backend.app.api.auth.get_jwt_secret",
                return_value=TEST_SECRET,
            ),
        ):
            response = self.client.post(
                "/api/test-session/write",
                headers={"X-CSRF-Token": csrf},
            )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

    def test_bearer_write_does_not_require_csrf(self):
        # Existing API-client behavior.
        with patch(
            "src.backend.app.api.auth.decode_access_token",
            return_value=USER_ID,
        ):
            response = self.client.post(
                "/api/test-session/write",
                headers={
                    "Authorization": "Bearer test-api-token"
                },
            )

        self.assertEqual(response.status_code, 200)

    def test_logout_rejects_missing_csrf(self):
        self.set_session_cookies()

        response = self.client.post(
            "/api/auth/logout"
        )

        self.assertEqual(response.status_code, 403)

    def test_logout_clears_cookies(self):
        token = "test-session-token"
        csrf = self.signed_csrf(token)

        self.set_session_cookies(
            session_token=token,
            csrf_token=csrf,
        )

        with patch(
            "src.backend.app.api.auth.get_jwt_secret",
            return_value=TEST_SECRET,
        ):
            response = self.client.post(
                "/api/auth/logout",
                headers={"X-CSRF-Token": csrf},
            )

        self.assertEqual(
            response.status_code,
            204,
            response.text,
        )

        cookie_headers = response.headers.get_list(
            "set-cookie"
        )

        session_header = next(
            header
            for header in cookie_headers
            if header.startswith("careerforge_session=")
        )

        csrf_header = next(
            header
            for header in cookie_headers
            if header.startswith("csrf_token=")
        )

        self.assertIn("max-age=0", session_header.lower())
        self.assertIn("path=/api", session_header.lower())

        self.assertIn("max-age=0", csrf_header.lower())
        self.assertIn("path=/", csrf_header.lower())

    def test_login_sets_expected_cookies(self):
        with (
            patch(
                "src.backend.app.api.routes.auth.verify_password",
                return_value=True,
            ),
            patch(
                "src.backend.app.api.routes.auth.create_access_token",
                return_value="test-jwt-token",
            ),
            patch(
                "src.backend.app.api.auth.get_jwt_secret",
                return_value=TEST_SECRET,
            ),
        ):
            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": "session-test@example.com",
                    "password": "test-password",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        cookie_headers = response.headers.get_list(
            "set-cookie"
        )

        session_header = next(
            header
            for header in cookie_headers
            if header.startswith("careerforge_session=")
        )

        csrf_header = next(
            header
            for header in cookie_headers
            if header.startswith("csrf_token=")
        )

        self.assertIn("httponly", session_header.lower())
        self.assertIn("samesite=lax", session_header.lower())
        self.assertIn("path=/api", session_header.lower())

        self.assertNotIn("httponly", csrf_header.lower())
        self.assertIn("samesite=lax", csrf_header.lower())

        self.assertEqual(
            response.json()["access_token"],
            "test-jwt-token",
        )


if __name__ == "__main__":
    unittest.main()
