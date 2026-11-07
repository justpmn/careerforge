
from sqlalchemy import inspect

from src.backend.app.database.models.user import User  # noqa: F401
from src.backend.app.database.models.career import Career  # noqa: F401
from src.backend.app.database.models.user_competency_assessment import (
    UserCompetencyAssessment,
)
from src.backend.app.database.session import get_db


def main():
    db_generator = get_db()
    db = next(db_generator)

    try:
        engine = db.get_bind()
        table = UserCompetencyAssessment.__table__

        if inspect(engine).has_table(table.name):
            print(f"Table already exists: {table.name}")
            return

        table.create(bind=engine, checkfirst=True)

        print(f"Table created: {table.name}")
        print("Existing application tables were not modified.")

    finally:
        db_generator.close()


if __name__ == "__main__":
    main()
