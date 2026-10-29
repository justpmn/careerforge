
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user_skill import UserSkill


router = APIRouter(
    prefix="/roadmaps",
    tags=["Roadmap Skill Evidence"],
)


@router.get("/skill-evidence/me")
def get_my_recorded_skills(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    records = db.execute(
        select(
            Skill.name,
            UserSkill.source,
        )
        .join(
            UserSkill,
            UserSkill.skill_id == Skill.id,
        )
        .where(UserSkill.user_id == user_id)
        .order_by(Skill.name)
    ).all()

    return {
        "skills": [
            {
                "name": name,
                "source": source,
                "status": "evidenced",
            }
            for name, source in records
        ]
    }
