from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.career import Career
from src.backend.app.database.models.recommendation import Recommendation
from src.backend.app.database.models.resume import Resume
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user import User
from src.backend.app.database.models.user_skill import UserSkill


def save_resume_analysis(
    db: Session,
    user_id: int,
    filename: str,
    extracted_text: str,
    extracted_skills: list[str],
    recommendations: list[dict],
    model_skills: list[str] | None = None,
    ignored_skills: list[str] | None = None,
    model_recommendations: list[dict] | None = None,
) -> Resume:
    """
    Save resume metadata, extracted user skills,
    and recommendation results in one transaction.
    """

    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise ValueError(
            f"User {user_id} does not exist."
        )

    extension = (
        Path(filename)
        .suffix
        .lower()
        .lstrip(".")
    )

    resume = Resume(
        user_id=user_id,
        file_name=filename,
        file_type=extension,
        storage_path="not_persisted",
        extracted_text=extracted_text,
        analysis_result={
            "extracted_skills": extracted_skills,
            "model_skills": model_skills if model_skills is not None else [],
            "ignored_skills": ignored_skills if ignored_skills is not None else [],
            "recommendations": recommendations,
            "model_recommendations": model_recommendations or [],
        },
    )

    db.add(resume)
    db.flush()

    skills = db.scalars(
        select(Skill).where(
            Skill.name.in_(
                extracted_skills
            )
        )
    ).all()

    for skill in skills:
        existing = db.scalar(
            select(UserSkill).where(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill.id,
            )
        )

        if existing:
            existing.source = "resume"
            continue

        db.add(
            UserSkill(
                user_id=user_id,
                skill_id=skill.id,
                source="resume",
                confidence_score=None,
            )
        )

    for item in recommendations:
        career = db.scalar(
            select(Career).where(
                Career.career_key
                == item["career_key"]
            )
        )

        if career is None:
            continue

        db.add(
            Recommendation(
                user_id=user_id,
                career_id=career.id,
                match_score=item["score"],
                explanation=None,
            )
        )

    db.commit()
    db.refresh(resume)

    return resume