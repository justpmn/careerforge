
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.user import User
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.competency_evidence import (
    CompetencyEvidence,
)
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)


ALLOWED_EVIDENCE_TYPES = {
    "project",
    "experience",
    "certification",
}


def create_competency_evidence(
    db: Session,
    user_id: int,
    career_key: str,
    competency_key: str,
    evidence_type: str,
    description: str,
) -> CompetencyEvidence:

    # Validate user.
    user = db.get(User, user_id)

    if user is None:
        raise ValueError(f"User {user_id} not found.")

    # Validate career.
    career = db.scalar(
        select(Career).where(
            Career.career_key == career_key
        )
    )

    if career is None:
        raise ValueError(
            f"Career '{career_key}' not found."
        )

    # Validate competency against reviewed profile.
    profile = CAREER_COMPETENCY_PROFILES.get(career_key)

    if profile is None:
        raise ValueError(
            f"No competency profile for '{career_key}'."
        )

    valid_keys = {
        group["key"]
        for group in profile
    }

    if competency_key not in valid_keys:
        raise ValueError(
            f"Invalid competency '{competency_key}' "
            f"for career '{career_key}'."
        )

    # Validate evidence type.
    if evidence_type not in ALLOWED_EVIDENCE_TYPES:
        raise ValueError(
            f"Unsupported evidence type: '{evidence_type}'."
        )

    description = description.strip()

    if not description:
        raise ValueError(
            "Evidence description cannot be empty."
        )

    # Store evidence as unverified self-report.
    evidence = CompetencyEvidence(
        user_id=user_id,
        career_id=career.id,
        competency_key=competency_key,
        evidence_type=evidence_type,
        description=description,
        verification_status="self_reported",
    )

    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


def get_competency_evidence(
    db: Session,
    user_id: int,
    career_key: str,
) -> list[CompetencyEvidence]:

    # Validate user.
    user = db.get(User, user_id)

    if user is None:
        raise ValueError(f"User {user_id} not found.")

    # Validate career.
    career = db.scalar(
        select(Career).where(
            Career.career_key == career_key
        )
    )

    if career is None:
        raise ValueError(
            f"Career '{career_key}' not found."
        )

    # Retrieve evidence for this user and career.
    records = db.scalars(
        select(CompetencyEvidence)
        .where(
            CompetencyEvidence.user_id == user_id,
            CompetencyEvidence.career_id == career.id,
        )
        .order_by(
            CompetencyEvidence.created_at.desc(),
            CompetencyEvidence.id.desc(),
        )
    ).all()

    return list(records)
