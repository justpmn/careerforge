from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.user_learning_progress import UserLearningProgress
from src.backend.app.database.session import get_db
from src.backend.app.services.career_competency_profiles import CAREER_COMPETENCY_PROFILES
from src.backend.app.services.learning_resource_service import (get_resources_for_skills, get_resources_for_competencies)

router = APIRouter(prefix="/roadmaps", tags=["Learning Progress"])


EXTRA_SKILLS = {"data_scientist": {"python"}}


class LearningUpdate(BaseModel):
    learned: bool


class LearningSkillResponse(BaseModel):
    skill_key: str
    learned: bool


def get_career_and_keys(db: Session, career_key: str):
    career = db.scalar(select(Career).where(Career.career_key == career_key))
    profile = CAREER_COMPETENCY_PROFILES.get(career_key)
    if career is None or profile is None:
        raise HTTPException(status_code=404, detail="Career roadmap not found.")

    allowed = {group["key"] for group in profile}
    allowed.update(EXTRA_SKILLS.get(career_key, set()))
    return career, allowed


@router.get("/learning-progress/{career_key}")
def read_learning_progress(
    career_key: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    career, allowed = get_career_and_keys(db, career_key)
    records = db.scalars(
        select(UserLearningProgress).where(
            UserLearningProgress.user_id == user_id,
            UserLearningProgress.career_id == career.id,
        )
    ).all()

    return {
        "career_key": career_key,
        "skills": [
            LearningSkillResponse(skill_key=record.skill_key, learned=record.learned)
            for record in records
            if record.skill_key in allowed
        ],
    }


@router.put(
    "/learning-progress/{career_key}/{skill_key}",
    response_model=LearningSkillResponse,
)
def update_learning_progress(
    payload: LearningUpdate,
    career_key: str,
    skill_key: str = Path(min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$"),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    career, allowed = get_career_and_keys(db, career_key)
    if skill_key not in allowed:
        raise HTTPException(status_code=404, detail="Skill not found in career roadmap.")

    record = db.get(UserLearningProgress, (user_id, career.id, skill_key))
    if record is None:
        record = UserLearningProgress(
            user_id=user_id,
            career_id=career.id,
            skill_key=skill_key,
            learned=payload.learned,
        )
        db.add(record)
    else:
        record.learned = payload.learned

    db.commit()
    return LearningSkillResponse(skill_key=skill_key, learned=record.learned)



# Maps visual-only foundation nodes to canonical
# skill names stored in PostgreSQL.
FOUNDATION_SKILL_NAMES = {
    "data_scientist": {
        "python": "Python",
    },
}


@router.get("/skill-resources/{career_key}/{skill_key}")
def read_skill_resources(
    career_key: str,
    skill_key: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # Check that the requested career and skill
    # belong to a recognized roadmap.
    _, allowed_keys = get_career_and_keys(
        db,
        career_key,
    )

    if skill_key not in allowed_keys:
        raise HTTPException(
            status_code=404,
            detail="Skill not found in career roadmap.",
        )

    # Foundation nodes correspond to canonical skills.
    canonical_name = FOUNDATION_SKILL_NAMES.get(
        career_key,
        {},
    ).get(skill_key)

    if canonical_name:
        resources = get_resources_for_skills(
            db,
            [canonical_name],
        )
    else:
        # Regular nodes correspond to competencies.
        resources = get_resources_for_competencies(
            db,
            [skill_key],
            career_key,
        ).get(skill_key, [])

    return {
        "career_key": career_key,
        "skill_key": skill_key,
        "resources": resources,
    }
