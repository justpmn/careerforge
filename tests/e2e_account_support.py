import hashlib
import re
import tempfile
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

def verification_token_path(email):
    if not re.fullmatch(
        r"cf-verify-e2e-[0-9a-f-]{36}@example\.com",
        email,
    ):
        raise ValueError("Invalid E2E verification email.")

    filename = hashlib.sha256(
        email.encode("utf-8")
    ).hexdigest() + ".token"

    return (
        Path(tempfile.gettempdir())
        / "careerforge_e2e_verification"
        / filename
    )


def capture_verification_email(recipient, token):
    if not recipient.startswith("cf-verify-e2e-"):
        return

    test_database_url()

    path = verification_token_path(recipient)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token, encoding="utf-8")


def take_verification_token(email):
    test_database_url()

    path = verification_token_path(email)

    if not path.is_file():
        raise RuntimeError("Verification token was not captured.")

    token = path.read_text(encoding="utf-8").strip()
    path.unlink()

    print(token)

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

def update_verification_token(email, action):
    verification_token_path(email)

    queries = {
        "expire-token": """
            UPDATE email_verification_tokens AS t
            SET expires_at = CURRENT_TIMESTAMP - INTERVAL '1 minute'
            FROM users AS u
            WHERE t.user_id = u.id
              AND lower(u.email) = :email
              AND u.email_verified_at IS NULL
        """,
        "age-token": """
            UPDATE email_verification_tokens AS t
            SET created_at = CURRENT_TIMESTAMP - INTERVAL '3 minutes'
            FROM users AS u
            WHERE t.user_id = u.id
              AND lower(u.email) = :email
              AND u.email_verified_at IS NULL
        """,
    }

    if action not in queries:
        raise ValueError("Invalid token adjustment.")

    engine = create_engine(test_database_url())

    try:
        with engine.begin() as db:
            result = db.execute(
                text(queries[action]),
                {"email": email.lower()},
            )

            if result.rowcount != 1:
                raise RuntimeError("E2E verification token not found.")
    finally:
        engine.dispose()

def promote_test_admin(email):
    import re

    if not re.fullmatch(
        r"cf-admin-mfa-e2e-[0-9a-f-]{36}@example\.com",
        email,
    ):
        raise ValueError("Invalid disposable admin email.")

    engine = create_engine(test_database_url())

    try:
        with engine.begin() as db:
            result = db.execute(
                text("""
                    UPDATE users
                    SET role = 'admin',
                        email_verified_at = CURRENT_TIMESTAMP
                    WHERE lower(email) = :email
                      AND role = 'user'
                      AND email_verified_at IS NULL
                      AND password_hash IS NOT NULL
                """),
                {"email": email.lower()},
            )

            if result.rowcount != 1:
                raise RuntimeError("Disposable admin not found.")
    finally:
        engine.dispose()

def expired_admin_mfa_challenge(email):
    import re
    import secrets
    from datetime import datetime, timedelta, timezone
    from src.backend.app.core import tokens

    if not re.fullmatch(
        r"cf-admin-mfa-e2e-[0-9a-f-]{36}@example\.com",
        email,
    ):
        raise ValueError("Invalid disposable admin email.")

    engine = create_engine(test_database_url())

    try:
        with engine.connect() as db:
            user_id = db.scalar(
                text("""
                    SELECT id FROM users
                    WHERE lower(email) = :email
                      AND role = 'admin'
                      AND email_verified_at IS NOT NULL
                """),
                {"email": email.lower()},
            )

        if user_id is None:
            raise RuntimeError("Disposable admin not found.")
    finally:
        engine.dispose()

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iss": tokens.JWT_ISSUER,
        "aud": tokens.JWT_AUDIENCE,
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=5),
        "jti": secrets.token_urlsafe(16),
        "token_type": "admin_mfa_challenge",
    }

    print(
        tokens.jwt.encode(
            payload,
            tokens.get_jwt_secret(),
            algorithm=tokens.JWT_ALGORITHM,
        )
    )
def serve():
    expected = make_url(test_database_url())

    from src.backend.app.api.routes import auth, email_verification
    from src.backend.app.main import app
    import uvicorn

    auth.send_verification_email = capture_verification_email
    email_verification.send_verification_email = capture_verification_email

    if hasattr(auth, "send_welcome_email"):
        auth.send_welcome_email = lambda *args, **kwargs: None

    uvicorn.run(app, host="127.0.0.1", port=18080)


if __name__ == "__main__":
    command = sys.argv[1]

    if command == "serve":
        serve()
    elif command == "activate":
        activate(sys.argv[2])
    elif command == "take-token":
        take_verification_token(sys.argv[2])
    elif command in {"expire-token", "age-token"}:
        update_verification_token(sys.argv[2], command)
    elif command == "promote-admin":
        promote_test_admin(sys.argv[2])
    elif command == "expired-mfa-challenge":
        expired_admin_mfa_challenge(sys.argv[2])
    else:
        raise SystemExit("Unknown command.")