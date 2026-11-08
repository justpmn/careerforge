
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user_skill import UserSkill
from src.backend.app.services.competency_gap_service import (analyze_competency_gaps)


ACTION_PRIORITY = {
    "review_submitted_evidence": 1,
    "review_resume_evidence": 2,
    "assess_competency": 3,
    "confirm_self_reported_skill": 4,
    "confirm_skill_experience": 5,
}

ACTION_DESCRIPTIONS = {
    "review_submitted_evidence": (
        "Review the user's submitted project, experience, "
        "or certification evidence."
    ),
    "review_resume_evidence": (
        "Review candidate competency evidence extracted "
        "from the user's CV."
    ),
    "assess_competency": (
        "Assess the user's existing experience before "
        "determining whether further learning is needed."
    ),
     "confirm_self_reported_skill": (
        "Confirm the user's self-reported experience "
        "before treating it as competency evidence."
    ),
    "confirm_skill_experience": (
        "Confirm whether the user has experience with "
        "any of the relevant skill alternatives."
    ),
}

RESOURCE_TECHNOLOGY_SKILLS = {
    "https://docs.pytest.org/en/stable/getting-started.html": {
        "Python",
    },
    "https://vitest.dev/guide/": {
        "JavaScript",
        "TypeScript",
        "Node.js",
    },
}


def select_relevant_resources(
    resources: list[dict],
    user_skills: set[str],
    limit: int = 2,
) -> list[dict]:
    """
    Prefer resources aligned with the user's
    recorded technology stack.

    If none match, retain the curated defaults.
    """

    relevant = [
        resource
        for resource in resources
        if RESOURCE_TECHNOLOGY_SKILLS.get(
            resource["url"], set()
        ) & user_skills
    ]

    if relevant:
        # Keep the original curated order.
        return relevant[:limit]

    return resources[:limit]


def explain_resource_recommendation(
    resource: dict,
    user_skills: set[str],
    career_name: str,
    competency_name: str,
) -> str:
    """
    Explain why a learning resource was selected.

    These explanations describe relevance, not
    verified skill deficiencies.
    """

    technology_skills = RESOURCE_TECHNOLOGY_SKILLS.get(
        resource["url"],
        set(),
    )

    matched_technologies = sorted(
        technology_skills & user_skills
    )

    if matched_technologies:
        return (
            f"Recommended because your recorded skills include "
            f"{', '.join(matched_technologies)}. "
            f"This resource can help you explore "
            f"{competency_name.lower()} using a familiar "
            f"technology."
        )

    if resource.get("matched_competency"):
        return (
            f"Selected for the {competency_name.lower()} "
            f"competency in the {career_name} career path. "
            f"Assess your existing experience before "
            f"deciding whether to study this topic."
        )

    matched_skills = resource.get("matched_skills", [])


    if matched_skills:
        return (
            f"This resource covers "
            f"{', '.join(matched_skills)}, "
            f"which is relevant to "
            f"{competency_name.lower()} "
            f"in the {career_name} career path. "
            f"Confirm your existing experience before "
            f"choosing a learning option."
        )


    return (
        f"This resource is a potential learning option "
        f"for {competency_name.lower()} in the "
        f"{career_name} career path."
    )

def generate_learning_roadmap(
    db: Session,
    user_id: int,
    career_key: str,
    focus_competencies: list[str] | None = None,
    optional_competencies: list[str] | None = None,
) -> dict:

    analysis = analyze_competency_gaps(
        db=db,
        user_id=user_id,
        career_key=career_key,
    )
    
    user_skills = set(
        db.scalars(
            select(Skill.name)
            .join(
                UserSkill,
                UserSkill.skill_id == Skill.id,
            )
            .where(UserSkill.user_id == user_id)
        ).all()
    )


    focus = set(focus_competencies or [])
    optional = set(optional_competencies or [])

    available_keys = {
        item["competency_key"]
        for item in analysis["competencies"]
    }

    unknown_keys = (focus | optional) - available_keys

    if unknown_keys:
        raise ValueError(
            f"Unknown competencies for {career_key}: "
            f"{sorted(unknown_keys)}"
        )

    if focus & optional:
        raise ValueError(
            "A competency cannot be both focused "
            "and optional."
        )

    steps = []

    for competency in analysis["competencies"]:
        action = competency["next_action"]

        if action == "no_immediate_action":
            continue

        key = competency["competency_key"]
        level = competency["level"]

        # These are roadmap priorities, not changes
        # to the reviewed career requirements.
        if key in optional:
            priority_group = "optional"
        elif key in focus:
            priority_group = "focused"
        elif level == "core":
            priority_group = "essential"
        else:
            priority_group = "recommended"
                    
        resources = list(competency["learning_resources"])

        # Prefer Docker when presenting deployment options.
        if key == "deployment":
            resources.sort(
                key=lambda resource: (
                    "Docker" not in resource.get(
                        "matched_skills", []
                    ),
                    resource["title"],
                )
            )

        # Select resources relevant to the user's skills.
        selected_resources = select_relevant_resources(
            resources,
            user_skills,
        )

        # Explain why each resource is recommended.
        explained_resources = []

        for resource in selected_resources:
            explained_resources.append({
                **resource,
                "recommendation_reason":
                    explain_resource_recommendation(
                        resource=resource,
                        user_skills=user_skills,
                        career_name=analysis["career_name"],
                        competency_name=competency["competency"],
                    ),
            })

        # Add the completed competency to the roadmap.
        steps.append({
            "competency_key": key,
            "competency": competency["competency"],
            "level": level,
            "status": competency["status"],
            "next_action": action,
            "description": ACTION_DESCRIPTIONS[action],
            "priority_group": priority_group,
            "learning_required": None,
            "suggested_resources": explained_resources,
        })



    group_order = {
        "focused": 0,
        "essential": 1,
        "recommended": 2,
        "optional": 3,
    }

    steps.sort(
        key=lambda step: (
            group_order[step["priority_group"]],
            ACTION_PRIORITY[step["next_action"]],
            step["competency"],
        )
    )

    for position, step in enumerate(steps, start=1):
        step["priority"] = position

    return {
        "user_id": user_id,
        "career_key": career_key,
        "career_name": analysis["career_name"],
        "total_steps": len(steps),
        "roadmap_type": "personalized_assessment_first",
        "learning_preferences": {
            "focus_competencies": sorted(focus),
            "optional_competencies": sorted(optional),
        },
        "steps": steps,
    }
