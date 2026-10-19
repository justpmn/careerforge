
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.learning_resource import (
    LearningResource,
)
from src.backend.app.database.models.learning_resource_skill import (
    LearningResourceSkill,
)


def get_resources_for_skills(
    db: Session,
    skill_names: list[str],
) -> list[dict]:

    # Remove duplicate skill names.
    skill_names = sorted(set(skill_names))

    if not skill_names:
        return []

    # Retrieve resources associated with canonical skills.
    rows = db.execute(
        select(
            LearningResource,
            Skill.name,
        )
        .join(
            LearningResourceSkill,
            LearningResourceSkill.learning_resource_id
            == LearningResource.id,
        )
        .join(
            Skill,
            Skill.id == LearningResourceSkill.skill_id,
        )
        .where(Skill.name.in_(skill_names))
        .order_by(
            LearningResource.title,
            Skill.name,
        )
    ).all()

    # Group results so a resource linked to several
    # skills appears only once.
    resources = {}

    for resource, skill_name in rows:

        if resource.id not in resources:
            resources[resource.id] = {
                "id": resource.id,
                "title": resource.title,
                "provider": resource.provider,
                "resource_type": resource.resource_type,
                "url": resource.url,
                "description": resource.description,
                "matched_skills": [],
            }

        resources[resource.id][
            "matched_skills"
        ].append(skill_name)

    return list(resources.values())
