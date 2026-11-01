
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.career import Career
from src.backend.app.database.models.user_competency_assessment import (
    UserCompetencyAssessment,
)
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)


def resolve_career(db: Session, career_key: str) -> Career:
    profile = CAREER_COMPETENCY_PROFILES.get(career_key)

    career = db.scalar(
        select(Career).where(Career.career_key == career_key)
    )

    if career is None or profile is None:
        raise ValueError("Career not found.")

    return career


def validate_competency(
    career_key: str,
    competency_key: str,
) -> None:
    profile = CAREER_COMPETENCY_PROFILES[career_key]

    allowed_keys = {
        item["key"]
        for item in profile
    }

    if competency_key not in allowed_keys:
        raise ValueError(
            "Competency not found in the selected career."
        )


def list_assessments(
    db: Session,
    user_id: int,
    career_key: str,
) -> list[UserCompetencyAssessment]:
    career = resolve_career(db, career_key)

    records = db.scalars(
        select(UserCompetencyAssessment).where(
            UserCompetencyAssessment.user_id == user_id,
            UserCompetencyAssessment.career_id == career.id,
        )
    ).all()

    return list(records)


def save_assessment(
    db: Session,
    user_id: int,
    career_key: str,
    competency_key: str,
    proficiency_level: str,
    notes: str | None,
) -> UserCompetencyAssessment:
    career = resolve_career(db, career_key)
    validate_competency(career_key, competency_key)

    if proficiency_level not in {
        "beginner",
        "intermediate",
        "advanced",
    }:
        raise ValueError("Invalid proficiency level.")

    clean_notes = notes.strip() if notes else None

    if not clean_notes:
        clean_notes = None

    record = db.get(
        UserCompetencyAssessment,
        (user_id, career.id, competency_key),
    )

    if record is None:
        record = UserCompetencyAssessment(
            user_id=user_id,
            career_id=career.id,
            competency_key=competency_key,
            proficiency_level=proficiency_level,
            notes=clean_notes,
        )
        db.add(record)
    else:
        record.proficiency_level = proficiency_level
        record.notes = clean_notes

    db.commit()
    db.refresh(record)

    return record
