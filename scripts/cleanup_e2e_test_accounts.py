
import argparse
import os
import re
from collections import Counter

from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import make_url


ACCOUNT_PATTERN = re.compile(
    r"^(cf-(?:"
    r"browser-e2e|browser-cv-e2e|roadmap-e2e|"
    r"competency-e2e|mentor-e2e|account-e2e"
    r")-)"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12}@example\.com$"
)

MAX_ACCOUNTS = 250


def main():
    parser = argparse.ArgumentParser(
        description="Clean CareerForge E2E test accounts."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit deletion instead of previewing.",
    )
    parser.add_argument(
        "--watermark",
        action="store_true",
        help="Print the highest existing user ID.",
    )
    parser.add_argument(
        "--after-id",
        type=int,
        default=0,
        help="Only select accounts with IDs above this value.",
    )
    args = parser.parse_args()

    if args.after_id < 0:
        parser.error("--after-id cannot be negative.")

    if args.watermark and (args.apply or args.after_id):
        parser.error(
            "--watermark cannot be combined with cleanup options."
        )

    database_url = os.environ.get(
        "CAREERFORGE_TEST_DATABASE_URL"
    )

    if not database_url:
        raise SystemExit(
            "CAREERFORGE_TEST_DATABASE_URL is required."
        )

    url = make_url(database_url)

    if (
        url.drivername != "postgresql+psycopg"
        or url.database != "careerforge_test"
        or url.host not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }
        or url.port not in (None, 5432)
    ):
        raise SystemExit(
            "Refusing to access a non-local test database."
        )

    engine = create_engine(database_url)

    try:
        with engine.begin() as connection:
            database = connection.scalar(
                text("SELECT current_database()")
            )

            if database != "careerforge_test":
                raise RuntimeError(
                    "Unexpected connected database."
                )

            if args.watermark:
                last_id = connection.scalar(
                    text("SELECT COALESCE(MAX(id), 0) FROM users")
                )
                print(last_id)
                return

            rows = connection.execute(
                text(
                    "SELECT id, email FROM users "
                    "WHERE email LIKE :pattern "
                    "AND id > :after_id "
                    "ORDER BY id FOR UPDATE"
                ),
                {
                    "pattern": "cf-%@example.com",
                    "after_id": args.after_id,
                },
            ).mappings().all()

            accounts = []
            counts = Counter()

            for row in rows:
                match = ACCOUNT_PATTERN.fullmatch(row["email"])

                if not match:
                    continue

                accounts.append(row)
                counts[match.group(1)] += 1

            if len(accounts) > MAX_ACCOUNTS:
                raise RuntimeError(
                    "Too many matching accounts. "
                    "Review the cleanup criteria."
                )

            print(f"Database: {database}")
            print(f"Matching E2E accounts: {len(accounts)}")

            if args.after_id:
                print(f"Only user IDs above: {args.after_id}")

            for prefix, count in sorted(counts.items()):
                print(f"  {prefix}: {count}")

            if not args.apply:
                print("\nDRY RUN: Nothing was deleted.")
                print("Use --apply to execute cleanup.")
                return

            if not accounts:
                print("\nNo accounts to delete.")
                return

            ids = [row["id"] for row in accounts]

            statement = text(
                "DELETE FROM users WHERE id IN :ids"
            ).bindparams(
                bindparam("ids", expanding=True)
            )

            result = connection.execute(
                statement,
                {"ids": ids},
            )

            if result.rowcount != len(ids):
                raise RuntimeError(
                    "Deleted row count did not match "
                    "the selected test accounts."
                )

            print(
                f"\nDeleted {result.rowcount} "
                "E2E test accounts."
            )

        print("Cleanup transaction committed.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
