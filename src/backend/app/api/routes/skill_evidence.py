
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user_skill import UserSkill


router = APIRouter(
    prefix="/roadmaps",
    tags=["Roadmap Skill Evidence"],
)


class ManualSkillCreate(BaseModel):
    skill_id: int = Field(gt=0)


def skill_response(skill: Skill, source: str) -> dict:
    return {
        "id": skill.id,
        "name": skill.name,
        "category": skill.category,
        "source": source,
        "status": (
            "self_reported"
            if source == "manual"
            else "evidenced"
        ),
    }


# Existing endpoint, with source-aware statuses.
@router.get("/skill-evidence/me")
def get_my_recorded_skills(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    records = db.execute(
        select(Skill, UserSkill.source)
        .join(
            UserSkill,
            UserSkill.skill_id == Skill.id,
        )
        .where(UserSkill.user_id == user_id)
        .order_by(Skill.name)
    ).all()

    return {
        "skills": [
            skill_response(skill, source)
            for skill, source in records
        ]
    }


# Search existing skills in the canonical database catalog.
@router.get("/skill-catalog")
def search_skill_catalog(
    query: str = Query(min_length=2, max_length=100),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    search_term = query.strip()

    if len(search_term) < 2:
        raise HTTPException(
            status_code=422,
            detail="Enter at least two characters.",
        )

    skills = db.scalars(
        select(Skill)
        .where(
            Skill.name.icontains(
                search_term,
                autoescape=True,
            )
        )
        .order_by(Skill.name)
        .limit(30)
    ).all()

    return {
        "query": search_term,
        "skills": [
            {
                "id": skill.id,
                "name": skill.name,
                "category": skill.category,
            }
            for skill in skills
        ],
    }


# Retrieve only skills manually added by the current user.
@router.get("/manual-skills")
def get_my_manual_skills(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    skills = db.scalars(
        select(Skill)
        .join(
            UserSkill,
            UserSkill.skill_id == Skill.id,
        )
        .where(
            UserSkill.user_id == user_id,
            UserSkill.source == "manual",
        )
        .order_by(Skill.name)
    ).all()

    return {
        "skills": [
            skill_response(skill, "manual")
            for skill in skills
        ],
    }


# Add a skill using its existing catalog ID.
@router.post("/manual-skills", status_code=201)
def add_manual_skill(
    payload: ManualSkillCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    skill = db.get(Skill, payload.skill_id)

    if skill is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found in the catalog.",
        )

    existing = db.get(
        UserSkill,
        (user_id, skill.id),
    )

    if existing is not None:
        if existing.source == "manual":
            raise HTTPException(
                status_code=409,
                detail="You have already added this skill.",
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "This skill is already recorded in your profile "
                "from another source."
            ),
        )

    record = UserSkill(
        user_id=user_id,
        skill_id=skill.id,
        source="manual",
        confidence_score=None,
    )

    db.add(record)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This skill is already recorded.",
        ) from error

    return skill_response(skill, "manual")


# Only manually added skills can be removed through this API.
@router.delete("/manual-skills/{skill_id}")
def remove_manual_skill(
    skill_id: int = Path(gt=0),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    record = db.get(
        UserSkill,
        (user_id, skill_id),
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Skill not found in your profile.",
        )

    if record.source != "manual":
        raise HTTPException(
            status_code=403,
            detail=(
                "Only manually added skills can be removed "
                "through this endpoint."
            ),
        )

    db.delete(record)
    db.commit()

    return {
        "skill_id": skill_id,
        "removed": True,
    }
