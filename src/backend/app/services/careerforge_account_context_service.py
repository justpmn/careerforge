from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.user import User
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user_skill import UserSkill
from src.backend.app.database.models.resume import Resume
from src.backend.app.database.models.user_learning_progress import (
    UserLearningProgress,
)
from src.backend.app.services.career_preference_service import (
    get_user_career_preferences,
    personalize_recommendations,
)
from src.backend.app.services.core_skill_coverage_service import (
    get_user_core_skill_coverage,
)
from src.backend.app.services.learning_roadmap_service import (
    generate_learning_roadmap,
)
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)


MAX_SKILLS = 15
MAX_CAREERS = 5
MAX_ROADMAP_STEPS = 5
MAX_RESOURCE_LINKS = 6


def _skills_context(db: Session, user_id: int) -> dict:
    rows = db.execute(
        select(Skill.name, UserSkill.source)
        .join(UserSkill, UserSkill.skill_id == Skill.id)
        .where(UserSkill.user_id == user_id)
    ).all()

    recorded = sorted({
        name for name, source in rows
        if source != "manual"
    })

    self_reported = sorted({
        name for name, source in rows
        if source == "manual"
    })

    return {
        "recorded": recorded[:MAX_SKILLS],
        "recorded_total": len(recorded),
        "self_reported": self_reported[:MAX_SKILLS],
        "self_reported_total": len(self_reported),
        "note": (
            "Recorded skills are not independently verified. "
            "Self-reported skills require confirmation."
        ),
    }


def _recommendations_context(
    db: Session,
    user_id: int,
) -> dict:
    resume = db.scalar(
        select(Resume)
        .where(
            Resume.user_id == user_id,
            Resume.analysis_result.is_not(None),
        )
        .order_by(Resume.id.desc())
        .limit(1)
    )

    if resume is None:
        return {
            "available": False,
            "reason": "No saved CV analysis",
        }

    analysis = resume.analysis_result or {}

    full_pool = analysis.get("model_recommendations")
    has_full_pool = isinstance(full_pool, list) and bool(full_pool)

    raw = (
        full_pool
        if has_full_pool
        else analysis.get("recommendations") or []
    )

    candidates = []

    for item in raw:
        if not isinstance(item, dict):
            continue

        key = item.get("career_key")
        score = item.get("score")

        if (
            isinstance(key, str)
            and isinstance(score, (int, float))
            and not isinstance(score, bool)
            and 0 <= score <= 1
        ):
            candidates.append({
                "career_key": key,
                "score": float(score),
            })

    ranked = personalize_recommendations(
        db=db,
        user_id=user_id,
        recommendations=candidates,
        top_k=MAX_CAREERS,
    )

    coverage = get_user_core_skill_coverage(
        db=db,
        user_id=user_id,
    )

    return {
        "available": bool(ranked),
        "source": "saved_random_forest_cv_analysis",
        "full_candidate_pool_available": has_full_pool,
        "ranking": [
            {
                "rank": item["rank"],
                "career_key": item["career_key"],
                "model_score": round(item["score"], 4),
                "documented_coverage_pct": (
                    coverage.get(
                        item["career_key"], {}
                    ).get("overall_percentage")
                ),
            }
            for item in ranked
        ],
        "notes": [
            "Model scores are classifier ranking signals.",
            "Documented coverage is not verified proficiency.",
            "Preferred careers are prioritized; avoided careers excluded.",
            "Browser-only sorting and Skip actions are not saved.",
        ],
    }


def _roadmap_context(
    db: Session,
    user_id: int,
    career_key: str | None,
    include_resources: bool,
) -> dict:
    if (
        not career_key
        or career_key not in CAREER_COMPETENCY_PROFILES
    ):
        return {
            "available": False,
            "reason": "No reviewed target career available",
        }

    career = db.scalar(
        select(Career).where(
            Career.career_key == career_key
        )
    )

    if career is None:
        return {"available": False}

    roadmap = generate_learning_roadmap(
        db=db,
        user_id=user_id,
        career_key=career_key,
    )

    progress = db.scalars(
        select(UserLearningProgress).where(
            UserLearningProgress.user_id == user_id,
            UserLearningProgress.career_id == career.id,
        )
    ).all()

    learned_keys = {
        record.skill_key
        for record in progress
        if record.learned
    }

    steps = roadmap["steps"]
    selected_steps = steps[:MAX_ROADMAP_STEPS]
    remaining_links = MAX_RESOURCE_LINKS if include_resources else 0

    summarized_steps = []

    for step in selected_steps:
        resources = []

        for resource in step.get("suggested_resources") or []:
            if remaining_links <= 0 or len(resources) >= 2:
                break

            title = resource.get("title")
            url = resource.get("url")

            if (
                not isinstance(title, str)
                or not title.strip()
                or not isinstance(url, str)
                or not url.startswith(("https://", "http://"))
            ):
                continue

            resources.append({
                "title": title,
                "provider": resource.get("provider"),
                "url": url,
            })
            remaining_links -= 1

        summarized_steps.append({
            "competency_key": step["competency_key"],
            "competency": step["competency"],
            "priority_group": step["priority_group"],
            "assessment_status": step["status"],
            "next_action": step["next_action"],
            "marked_learned": (
                step["competency_key"] in learned_keys
            ),
            "resources": resources,
        })

    return {
        "available": True,
        "career_key": career_key,
        "career_name": roadmap["career_name"],
        "total_active_steps": len(steps),
        "marked_learned_steps": sum(
            step["competency_key"] in learned_keys
            for step in steps
        ),
        "steps": summarized_steps,
        "omitted_steps": max(
            0, len(steps) - len(selected_steps)
        ),
        "note": (
            "Marked as learned is user-tracked progress, "
            "not independent competency verification. "
            "Resources come from CareerForge's roadmap mappings."
        ),
    }


def build_account_mentor_context(
    db: Session,
    user_id: int,
    career_key: str | None = None,
    include_resources: bool = False,
) -> dict:
    user = db.get(User, user_id)

    if user is None:
        raise ValueError("Authenticated user not found.")

    target_career = None

    if user.target_career_id is not None:
        target_career = db.get(
            Career,
            user.target_career_id,
        )

    active_career_key = (
        career_key
        or (
            target_career.career_key
            if target_career is not None
            else None
        )
    )

    preferences = get_user_career_preferences(
        db=db,
        user_id=user_id,
    )

    return {
        "source": "careerforge_authenticated_account",
        "selected_target_career": (
            target_career.career_key
            if target_career is not None
            else None
        ),
        "active_discussion_career": active_career_key,
        "career_preferences": {
            "preferred": preferences["preferred"][:10],
            "avoided": preferences["avoid"][:10],
        },
        "skills": _skills_context(db, user_id),
        "recommendations": _recommendations_context(
            db, user_id
        ),
        "roadmap": _roadmap_context(
            db=db,
            user_id=user_id,
            career_key=active_career_key,
            include_resources=include_resources,
        ),
    }