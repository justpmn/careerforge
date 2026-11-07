
"""
Seed the full CareerForge reference catalog into careerforge_test.

Uses existing career, skill and career-skill CSVs.
Never writes to the development database.
Safe to rerun.
"""

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings


TEST_DATABASE = "careerforge_test"


def main():
    source_url = make_url(settings.database_url)

    if source_url.drivername != "postgresql+psycopg":
        raise RuntimeError("Expected PostgreSQL with psycopg.")

    if source_url.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise RuntimeError("Only local PostgreSQL is allowed.")

    if source_url.port not in {None, 5432}:
        raise RuntimeError("Unexpected PostgreSQL port.")

    if source_url.database not in {
        "careerforge",
        TEST_DATABASE,
    }:
        raise RuntimeError("Unexpected source database.")

    test_url = source_url.set(database=TEST_DATABASE)

    engine = create_engine(
        test_url,
        pool_pre_ping=True,
    )

    try:
        with engine.connect() as connection:
            actual_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        if actual_database != TEST_DATABASE:
            raise RuntimeError(
                "Database safety check failed."
            )

        # Import after the safety checks.
        from scripts.seed_reference_data import (
            CAREERS_PATH,
            SKILLS_PATH,
            CAREER_SKILLS_PATH,
            seed_careers,
            seed_skills,
            seed_career_skills,
        )

        from src.backend.app.database.models.career import Career
        from src.backend.app.database.models.skill import Skill
        from src.backend.app.database.models.career_skill import (
            CareerSkill,
        )

        required_files = [
            CAREERS_PATH,
            SKILLS_PATH,
            CAREER_SKILLS_PATH,
        ]

        for path in required_files:
            if not path.is_file():
                raise FileNotFoundError(
                    f"Missing reference dataset: {path}"
                )

        print("Seeding full integration catalog...")
        print(f"Database: {TEST_DATABASE}")

        with Session(engine) as db:
            try:
                seed_careers(db)
                seed_skills(db)
                seed_career_skills(db)

                db.commit()

            except Exception:
                db.rollback()
                raise

        with Session(engine) as db:
            career_count = db.scalar(
                select(func.count()).select_from(Career)
            )

            skill_count = db.scalar(
                select(func.count()).select_from(Skill)
            )

            edge_count = db.scalar(
                select(func.count()).select_from(CareerSkill)
            )

        if not all([
            career_count,
            skill_count,
            edge_count,
        ]):
            raise RuntimeError(
                "Catalog seeding produced incomplete reference data."
            )

        print()
        print("FULL INTEGRATION CATALOG")
        print("------------------------")
        print(f"Database: {TEST_DATABASE}")
        print(f"Careers: {career_count}")
        print(f"Skills: {skill_count}")
        print(f"Career-skill links: {edge_count}")
        print("Reference seeding completed successfully.")
        print("------------------------")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
