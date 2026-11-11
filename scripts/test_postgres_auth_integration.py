
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings


# CRITICAL: Validate the database before importing FastAPI
# or the application's database session module.
url = make_url(settings.database_url)

if (
    url.drivername != "postgresql+psycopg"
    or url.database != "careerforge_test"
    or url.host not in {"localhost", "127.0.0.1", "::1"}
    or url.port not in {None, 5432}
):
    raise RuntimeError(
        "Integration tests require local careerforge_test. "
        "Refusing to use another database."
    )


from src.backend.app.database.session import engine, get_db
from src.backend.app.database.models.user import User
from src.backend.app.main import app


PASSWORD = "Test-Only-CareerForge-Password-2026!"


class TestPostgresAuthIntegration(unittest.TestCase):

    def setUp(self):
        # All test writes run inside an outer transaction.
        self.connection = engine.connect()
        self.transaction = self.connection.begin()

        database_name = self.connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if database_name != "careerforge_test":
            self.transaction.rollback()
            self.connection.close()
            raise RuntimeError("Database safety check failed.")

        def override_get_db():
            # Endpoint commits only release savepoints.
            # The outer transaction remains available for
            # rollback after each test.
            with Session(
                bind=self.connection,
                join_transaction_mode="create_savepoint",
            ) as session:
                yield session

        self.previous_override = app.dependency_overrides.get(
            get_db
        )

        app.dependency_overrides[get_db] = override_get_db

        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

        if self.previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = (
                self.previous_override
            )

        try:
            # No test users survive this rollback.
            if self.transaction.is_active:
                self.transaction.rollback()
        finally:
            self.connection.close()

    def new_email(self):
        return f"cf-integration-{uuid4().hex}@example.com"

    def register(self, client=None, name="Integration User"):
        client = client or self.client

        response = client.post(
            "/api/auth/register",
            json={
                "full_name": name,
                "email": self.new_email(),
                "password": PASSWORD,
            },
        )

        self.assertEqual(
            response.status_code,
            201,
            response.text,
        )

        user = response.json()

        result = self.connection.execute(
            text("""
                UPDATE users
                SET email_verified_at = CURRENT_TIMESTAMP
                WHERE id = :id AND email = :email
            """),
            {"id": user["id"], "email": user["email"]},
        )

        self.assertEqual(result.rowcount, 1)
        return user

    def login(self, email, client=None):
        client = client or self.client

        response = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": PASSWORD,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        return response.json()["access_token"]

    def test_registration_and_real_database_read(self):
        user = self.register()

        # Verify the record using a fresh SQLAlchemy
        # session bound to the isolated test transaction.
        with Session(
            bind=self.connection,
            join_transaction_mode="create_savepoint",
        ) as session:

            stored = session.get(User, user["id"])

            self.assertIsNotNone(stored)
            self.assertEqual(
                stored.email,
                user["email"],
            )

            self.assertNotEqual(
                stored.password_hash,
                PASSWORD,
            )

    def test_real_login_and_authenticated_identity(self):
        user = self.register()

        token = self.login(user["email"])

        response = self.client.get("/api/auth/me")

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        self.assertEqual(
            response.json()["id"],
            str(user["id"]),
        )

        # Verify Bearer authentication using the
        # actual issued JWT.
        bearer_client = TestClient(app)

        try:
            response = bearer_client.get(
                "/api/auth/me",
                headers={
                    "Authorization": f"Bearer {token}"
                },
            )

            self.assertEqual(
                response.status_code,
                200,
                response.text,
            )

        finally:
            bearer_client.close()

    def test_two_real_users_have_separate_sessions(self):
        user_a = self.register(name="User A")
        self.login(user_a["email"])

        client_b = TestClient(app)

        try:
            user_b = self.register(
                client=client_b,
                name="User B",
            )

            self.login(
                user_b["email"],
                client=client_b,
            )

            response_a = self.client.get("/api/auth/me")
            response_b = client_b.get("/api/auth/me")

            self.assertEqual(response_a.status_code, 200)
            self.assertEqual(response_b.status_code, 200)

            self.assertEqual(
                response_a.json()["id"],
                str(user_a["id"]),
            )

            self.assertEqual(
                response_b.json()["id"],
                str(user_b["id"]),
            )

            self.assertNotEqual(
                user_a["id"],
                user_b["id"],
            )

            # User A must not access User B's roadmap.
            response = self.client.get(
                f"/api/roadmaps/users/{user_b['id']}"
                "/careers/data_engineer"
            )

            self.assertEqual(
                response.status_code,
                403,
                response.text,
            )

        finally:
            client_b.close()

    def test_real_cookie_csrf_and_logout(self):
        user = self.register()
        self.login(user["email"])

        # Cookie-authenticated writes require CSRF.
        missing_csrf = self.client.post(
            "/api/auth/onboarding/complete"
        )

        self.assertEqual(
            missing_csrf.status_code,
            403,
            missing_csrf.text,
        )

        csrf = self.client.cookies.get("csrf_token")
        self.assertIsNotNone(csrf)

        logout = self.client.post(
            "/api/auth/logout",
            headers={"X-CSRF-Token": csrf},
        )

        self.assertEqual(
            logout.status_code,
            204,
            logout.text,
        )

        after_logout = self.client.get("/api/auth/me")

        self.assertEqual(
            after_logout.status_code,
            401,
            after_logout.text,
        )


if __name__ == "__main__":
    unittest.main()
