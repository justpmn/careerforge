
import argparse

from sqlalchemy import func, select

from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from src.backend.app.core.admin_logging import record_system_event


def main():
    parser = argparse.ArgumentParser(
        description="Promote an existing CareerForge user."
    )

    parser.add_argument(
        "--email",
        required=True,
        help="Email of the existing account.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the promotion. Otherwise, dry run.",
    )

    args = parser.parse_args()

    email = args.email.strip().lower()

    if not email:
        raise SystemExit("Email cannot be empty.")

    db_generator = get_db()
    db = next(db_generator)

    try:
        user = db.scalar(
            select(User).where(
                func.lower(User.email) == email
            )
        )

        if user is None:
            raise SystemExit("Account not found.")

        print(f"Account ID: {user.id}")
        print(f"Current role: {user.role}")

        if user.role == "admin":
            print("Account already has administrator access.")
            return

        if not args.apply:
            print(
                "Dry run only. Use --apply to confirm promotion."
            )
            return

        confirmation = input(
            "Type PROMOTE to grant administrator access: "
        )

        if confirmation != "PROMOTE":
            print("Promotion cancelled.")
            return

        user.role = "admin"

        db.commit()

        record_system_event(
            category="security",
            action="development_admin_bootstrapped",
            severity="WARNING",
        )

        print("Administrator access granted.")

    finally:
        db_generator.close()


if __name__ == "__main__":
    main()
