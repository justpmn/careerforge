
"""
Seed minimal reference data for CareerForge integration tests.

Only writes to careerforge_test.
Never writes to the development database.
Safe to rerun without creating duplicate records.
"""

from sqlalchemy import (
    create_engine,
    inspect,
    select,
    text,
)
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user import User
from src.backend.app.database.models.user_competency_assessment import (
    UserCompetencyAssessment,
)
from src.backend.app.database.models.user_learning_progress import (
    UserLearningProgress,
)
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)


TEST_DATABASE = "careerforge_test"
CAREER_KEY = "data_engineer"


def main():
    source_url = make_url(settings.database_url)

    if source_url.drivername != "postgresql+psycopg":
        raise RuntimeError(
            "Expected PostgreSQL with psycopg."
        )

    if source_url.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise RuntimeError(
            "Refusing a non-local PostgreSQL server."
        )

    if source_url.port not in {None, 5432}:
        raise RuntimeError(
            "Unexpected PostgreSQL port."
        )

    if source_url.database not in {
        "careerforge",
        TEST_DATABASE,
    }:
        raise RuntimeError(
            "Unexpected source database."
        )

    test_url = source_url.set(
        database=TEST_DATABASE,
    )

    if not CAREER_COMPETENCY_PROFILES.get(CAREER_KEY):
        raise RuntimeError(
            "Data Engineer competency profile not found."
        )

    engine = create_engine(
        test_url,
        pool_pre_ping=True,
    )

    try:
        # Verify the actual database before performing writes.
        with engine.connect() as connection:
            actual_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        if actual_database != TEST_DATABASE:
            raise RuntimeError(
                "Database safety check failed."
            )

        # Check that migrations created the required tables.
        existing_tables = set(
            inspect(engine).get_table_names(
                schema="public"
            )
        )

        required_tables = {
            Career.__tablename__,
            Skill.__tablename__,
            User.__tablename__,
            UserCompetencyAssessment.__tablename__,
            UserLearningProgress.__tablename__,
        }

        missing_tables = (
            required_tables - existing_tables
        )

        if missing_tables:
            raise RuntimeError(
                "Missing integration database tables: "
                + ", ".join(sorted(missing_tables))
                + ". Check Alembic migrations."
            )

        with Session(engine) as db:
            career = db.scalar(
                select(Career).where(
                    Career.career_key == CAREER_KEY
                )
            )

            if career is None:
                career = Career(
                    career_key=CAREER_KEY,
                    name="Data Engineer",
                    description=(
                        "Designs and maintains data pipelines "
                        "and data processing infrastructure."
                    ),
                )
                db.add(career)
                print("Added career: Data Engineer")
            else:
                print("Career already exists: Data Engineer")

            for name, category in [
                ("Python", "Programming"),
                ("SQL", "Databases"),
            ]:
                existing_skill = db.scalar(
                    select(Skill).where(
                        Skill.name == name
                    )
                )

                if existing_skill is None:
                    db.add(
                        Skill(
                            name=name,
                            category=category,
                        )
                    )
                    print(f"Added skill: {name}")
                else:
                    print(f"Skill already exists: {name}")

            db.commit()

        with Session(engine) as db:
            career_count = db.scalar(
                select(Career)
                .where(Career.career_key == CAREER_KEY)
            )

            skills = db.scalars(
                select(Skill).where(
                    Skill.name.in_(["Python", "SQL"])
                )
            ).all()

        print()
        print("INTEGRATION REFERENCE DATA")
        print("--------------------------")
        print(f"Database: {TEST_DATABASE}")
        print(f"Career ready: {career_count is not None}")
        print(f"Skills available: {len(skills)}/2")
        print("Development database: not modified")
        print("--------------------------")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
