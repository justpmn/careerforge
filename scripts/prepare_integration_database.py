
"""
Prepare CareerForge's isolated PostgreSQL integration database.

Safety rules:
- Local PostgreSQL only.
- Expected development database: careerforge.
- Test database: careerforge_test.
- Never drops or truncates a database.
- Never runs migrations against the development database.
"""

import os
import subprocess
import sys
from pathlib import Path

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

from src.backend.app.core.config import settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEVELOPMENT_DATABASE = "careerforge"
TEST_DATABASE = "careerforge_test"

ALLOWED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
}


def main():
    source_url = make_url(settings.database_url)

    # Reject unexpected database configurations.
    if source_url.drivername != "postgresql+psycopg":
        raise RuntimeError(
            "Expected PostgreSQL using the psycopg driver."
        )

    if source_url.host not in ALLOWED_HOSTS:
        raise RuntimeError(
            "Refusing to connect to a non-local database."
        )

    if source_url.database != DEVELOPMENT_DATABASE:
        raise RuntimeError(
            "Expected source database 'careerforge'. "
            "Refusing to modify an unexpected database."
        )

    test_url = source_url.set(
        database=TEST_DATABASE,
    )

    connection_args = {
        "host": source_url.host,
        "port": source_url.port or 5432,
        "user": source_url.username,
        "password": source_url.password,
        "connect_timeout": 10,
    }

    print("Checking isolated test database...")

    # Connect only to PostgreSQL's maintenance database.
    with psycopg.connect(
        dbname="postgres",
        autocommit=True,
        **connection_args,
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (TEST_DATABASE,),
            )

            exists = cursor.fetchone() is not None

            if exists:
                print(
                    f"Database '{TEST_DATABASE}' already exists."
                )

            else:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(TEST_DATABASE)
                    )
                )

                print(
                    f"Created database '{TEST_DATABASE}'."
                )

    print("Applying Alembic migrations to test database...")

    # A fresh Python process ensures Alembic reads
    # DATABASE_URL before importing the application.
    environment = os.environ.copy()

    environment["DATABASE_URL"] = (
        test_url.render_as_string(
            hide_password=False
        )
    )

    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "upgrade",
            "head",
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )

    # Verify the migration revision in the test DB.
    with psycopg.connect(
        dbname=TEST_DATABASE,
        **connection_args,
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT version_num FROM alembic_version"
            )

            revisions = [
                row[0]
                for row in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public'
                """
            )

            table_count = cursor.fetchone()[0]

    print()
    print("INTEGRATION DATABASE PREPARATION")
    print("--------------------------------")
    print(f"Database: {TEST_DATABASE}")
    print(f"Migration revisions: {revisions}")
    print(f"Public tables: {table_count}")
    print("Development database: untouched")
    print("--------------------------------")


if __name__ == "__main__":
    main()
