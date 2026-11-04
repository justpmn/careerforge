
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy.engine import make_url

from src.backend.app.core.config import settings


ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE = "careerforge_test"


def main():
    source = make_url(settings.database_url)

    if source.drivername != "postgresql+psycopg":
        raise RuntimeError("Expected PostgreSQL with psycopg.")

    if source.host not in {"localhost", "127.0.0.1", "::1"}:
        raise RuntimeError("Only local PostgreSQL is allowed.")

    if source.port not in {None, 5432}:
        raise RuntimeError("Unexpected PostgreSQL port.")

    if source.database not in {"careerforge", TEST_DATABASE}:
        raise RuntimeError("Unexpected source database.")

    test_url = source.set(database=TEST_DATABASE)

    environment = os.environ.copy()
    environment["DATABASE_URL"] = test_url.render_as_string(
        hide_password=False
    )

    print(f"Target database: {TEST_DATABASE}", flush=True)
    print("Starting transaction-isolated integration tests...", flush=True)


    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "scripts.test_postgres_auth_integration",
            "scripts.test_postgres_persistence",
            "-v",
        ],
        cwd=ROOT,
        env=environment,
        check=False,
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
