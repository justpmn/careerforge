from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.user import User
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.career_skill import CareerSkill
from src.backend.app.database.models.user_skill import UserSkill


def compare_user_career_skills(
    db: Session,
    user_id: int,
    career_key: str,
) -> dict:
    """
    Compare a user's recorded skills against
    skills associated with a selected career.
    """
    user = db.get(User, user_id)

    if user is None:
        raise ValueError(f"User {user_id} not found.")

    career = db.scalar(
        select(Career).where(
            Career.career_key == career_key
        )
    )

    if career is None:
        raise ValueError(
            f"Career '{career_key}' not found."
        )

    career_skills = db.execute(
        select(
            Skill.id,
            Skill.name,
            CareerSkill.importance_level,
        )
        .join(
            CareerSkill,
            CareerSkill.skill_id == Skill.id,
        )
        .where(
            CareerSkill.career_id == career.id
        )
        .order_by(Skill.name)
    ).all()

    # 4. Retrieve the user's recorded skill IDs.
    user_skill_ids = set(
        db.scalars(
            select(UserSkill.skill_id).where(
                UserSkill.user_id == user_id
            )
        ).all()
    )

    # 5. Compare the two sets.
    matched_skills = []
    potential_gaps = []

    for skill_id, skill_name, importance in career_skills:
        if skill_id in user_skill_ids:
            matched_skills.append(skill_name)
        else:
            potential_gaps.append(skill_name)

    return {
        "user_id": user_id,
        "career_key": career_key,
        "career_name": career.name,
        "total_career_skills": len(career_skills),
        "matched_count": len(matched_skills),
        "potential_gap_count": len(potential_gaps),
        "matched_skills": matched_skills,
        "potential_gaps": potential_gaps,
    }