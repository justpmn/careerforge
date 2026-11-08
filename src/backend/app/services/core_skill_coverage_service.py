from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user_skill import UserSkill
from src.backend.app.database.models.resume import Resume
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)


def calculate_core_skill_coverage(
    profile: list[dict],
    catalog: set[str],
    recorded_skills: set[str],
    manual_skills: set[str],
) -> dict:
    total = {"core": 0, "supporting": 0}
    matched = {"core": 0, "supporting": 0}
    self_reported = {"core": 0, "supporting": 0}
    manual_review = {"core": 0, "supporting": 0}
    unmapped = 0

    for group in profile:
        level = group.get("level")

        if level not in total:
            continue

        total[level] += 1

        if group.get("assessment") == "manual_review":
            manual_review[level] += 1
            continue

        alternatives = set(group.get("any_of") or [])
        available = alternatives & catalog

        if not available:
            unmapped += 1
            continue

        if available & recorded_skills:
            matched[level] += 1
        elif available & manual_skills:
            self_reported[level] += 1

    denominator = 2 * total["core"] + total["supporting"]
    numerator = 2 * matched["core"] + matched["supporting"]

    overall = (
        round(100 * numerator / denominator, 1)
        if denominator > 0 and unmapped == 0
        else None
    )

    core = (
        round(100 * matched["core"] / total["core"], 1)
        if total["core"] > 0 and unmapped == 0
        else None
    )

    return {
        "percentage": core,
        "overall_percentage": overall,
        "matched_core": matched["core"],
        "total_core": total["core"],
        "matched_supporting": matched["supporting"],
        "total_supporting": total["supporting"],
        "self_reported_core": self_reported["core"],
        "self_reported_supporting": self_reported["supporting"],
        "manual_review_core": manual_review["core"],
        "manual_review_supporting": manual_review["supporting"],
        "missing_catalog_core": unmapped,
        "unmapped_groups": unmapped,
    }
    
def get_user_core_skill_coverage(
    db: Session,
    user_id: int,
) -> dict[str, dict]:
    catalog = set(db.scalars(select(Skill.name)).all())

    rows = db.execute(
        select(Skill.name, UserSkill.source)
        .join(
            UserSkill,
            UserSkill.skill_id == Skill.id,
        )
        .where(UserSkill.user_id == user_id)
    ).all()

    recorded_skills = {
        name for name, source in rows
        if source != "manual"
    }

    manual_skills = {
        name for name, source in rows
        if source == "manual"
    }

    latest_analysis = db.scalar(
        select(Resume.analysis_result)
        .where(
            Resume.user_id == user_id,
            Resume.analysis_result.is_not(None),
        )
        .order_by(Resume.id.desc())
        .limit(1)
    )

    if isinstance(latest_analysis, dict):
        extracted = latest_analysis.get("extracted_skills")

        if isinstance(extracted, list):
            recorded_skills.difference_update({
                name for name, source in rows
                if source == "resume"
            })

            recorded_skills.update({
                name for name in extracted
                if isinstance(name, str) and name in catalog
            })

    return {
        career_key: calculate_core_skill_coverage(
            profile=profile,
            catalog=catalog,
            recorded_skills=recorded_skills,
            manual_skills=manual_skills,
        )
        for career_key, profile
        in CAREER_COMPETENCY_PROFILES.items()
    }