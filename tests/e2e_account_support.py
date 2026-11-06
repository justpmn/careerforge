
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_database_url():
    raw = os.getenv("CAREERFORGE_TEST_DATABASE_URL")
    if not raw:
        raise RuntimeError("CAREERFORGE_TEST_DATABASE_URL is required.")

    url = make_url(raw)
    if (
        url.get_backend_name() != "postgresql"
        or url.database != "careerforge_test"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
    ):
        raise RuntimeError("Only local careerforge_test is allowed.")

    return raw


def activate(email):
    allowed_prefixes = (
    "cf-browser-e2e-",
    "cf-account-e2e-",
    "cf-browser-cv-e2e-",
    "cf-competency-e2e-",
    "cf-mentor-e2e-",
    "cf-roadmap-e2e-",
    )

    if not (
        email.startswith(allowed_prefixes)
        and email.endswith("@example.com")
    ):
        raise ValueError("Invalid E2E test account email.")

    engine = create_engine(test_database_url())

    try:
        with engine.begin() as db:
            result = db.execute(
                text("""
                    UPDATE users
                    SET email_verified_at = CURRENT_TIMESTAMP
                    WHERE lower(email) = :email
                      AND email_verified_at IS NULL
                """),
                {"email": email.lower()},
            )

            if result.rowcount != 1:
                raise RuntimeError("Unverified test user not found.")
    finally:
        engine.dispose()


def serve():
    expected = make_url(test_database_url())

    from src.backend.app.core.config import settings

    actual = make_url(settings.database_url)

    if (
        actual.database != expected.database
        or actual.host != expected.host
        or actual.username != expected.username
        or actual.password != expected.password
        or actual.port != expected.port
    ):
        raise RuntimeError("Backend database does not match test database.")

    from src.backend.app.api.routes import auth
    from src.backend.app.main import app
    import uvicorn

    auth.send_verification_email = lambda recipient, token: None

    uvicorn.run(app, host="127.0.0.1", port=18080)


if __name__ == "__main__":
    command = sys.argv[1]

    if command == "serve":
        serve()
    elif command == "activate":
        activate(sys.argv[2])
    else:
        raise SystemExit("Unknown command.")
