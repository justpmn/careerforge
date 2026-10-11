import pandas as pd
from sqlalchemy import select

from src.backend.app.database.models.career import Career
from src.backend.app.database.models.career_skill import CareerSkill
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.session import SessionLocal
from src.preprocessing.paths import PROCESSED_DATA_DIR


CAREERS_PATH = PROCESSED_DATA_DIR / "careers.csv"
SKILLS_PATH = PROCESSED_DATA_DIR / "final_skill_vocabulary.csv"
CAREER_SKILLS_PATH = PROCESSED_DATA_DIR / "final_career_skills.csv"


def seed_careers(db) -> None:
    careers = pd.read_csv(CAREERS_PATH)

    for row in careers.itertuples(index=False):
        existing = db.scalar(
            select(Career).where(
                Career.career_key == row.career_key
            )
        )

        if existing:
            existing.name = row.career_name
            continue

        db.add(
            Career(
                career_key=row.career_key,
                name=row.career_name,
            )
        )

    db.flush()


def seed_skills(db) -> None:
    skills = pd.read_csv(SKILLS_PATH)

    for row in skills.itertuples(index=False):
        existing = db.scalar(
            select(Skill).where(
                Skill.name == row.canonical_skill
            )
        )

        if existing:
            existing.category = row.categories
            continue

        db.add(
            Skill(
                name=row.canonical_skill,
                category=row.categories,
            )
        )

    db.flush()


def seed_career_skills(db) -> None:
    edges = pd.read_csv(CAREER_SKILLS_PATH)

    careers = {
        career.career_key: career.id
        for career in db.scalars(
            select(Career)
        ).all()
    }

    skills = {
        skill.name: skill.id
        for skill in db.scalars(
            select(Skill)
        ).all()
    }

    added = 0
    skipped = 0

    for row in edges.itertuples(index=False):
        career_id = careers.get(row.career_key)
        skill_id = skills.get(row.canonical_skill)

        if career_id is None or skill_id is None:
            skipped += 1
            continue

        existing = db.scalar(
            select(CareerSkill).where(
                CareerSkill.career_id == career_id,
                CareerSkill.skill_id == skill_id,
            )
        )

        if existing:
            continue

        db.add(
            CareerSkill(
                career_id=career_id,
                skill_id=skill_id,
                importance_level=1,
            )
        )

        added += 1

    print(f"Career-skill links added: {added}")
    print(f"Career-skill links skipped: {skipped}")


def main():
    db = SessionLocal()

    try:
        print("Seeding careers...")
        seed_careers(db)

        print("Seeding skills...")
        seed_skills(db)

        print("Seeding career-skill links...")
        seed_career_skills(db)

        db.commit()

        print("\nReference data seeded successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()