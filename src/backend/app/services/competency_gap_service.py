from sqlalchemy import select
from sqlalchemy.orm import Session
from src.backend.app.database.models.user import User
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.user_skill import UserSkill
from src.backend.app.database.models.career_skill import CareerSkill
from src.backend.app.database.models.resume import Resume
from src.preprocessing.competency_evidence_extractor import (extract_competency_evidence)
from src.backend.app.services.career_competency_profiles import (CAREER_COMPETENCY_PROFILES)

def analyze_competency_gaps(
    db: Session,
    user_id: int,
    career_key: str,
) -> dict:

    user = db.get(User, user_id)

    if user is None:
        raise ValueError(f"User {user_id} not found.")

    career = db.scalar(
        select(Career).where(
            Career.career_key == career_key
        )
    )

    if career is None:
        raise ValueError(f"Career '{career_key}' not found.")

    profile = CAREER_COMPETENCY_PROFILES.get(career_key)

    if profile is None:
        raise ValueError(
            f"No reviewed competency profile for '{career_key}'."
        )

    # Registered canonical skills.
    catalog = set(
        db.scalars(select(Skill.name)).all()
    )

    # Skills recorded for the user.
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

    # Skills connected to the career in our KG.
    graph_skills = set(
        db.scalars(
            select(Skill.name)
            .join(
                CareerSkill,
                CareerSkill.skill_id == Skill.id,
            )
            .where(CareerSkill.career_id == career.id)
        ).all()
    )
        # Retrieve the user's most recent resume.
    resume = db.scalar(
        select(Resume)
        .where(
            Resume.user_id == user_id,
            Resume.extracted_text.is_not(None),
        )
        .order_by(
            Resume.uploaded_at.desc(),
            Resume.id.desc(),
        )
    )

    # Extract evidence from resume descriptions.
    resume_evidence = {}

    if resume and resume.extracted_text:
        resume_evidence = extract_competency_evidence(
            resume.extracted_text
        )

    results = []

    for group in profile:
        # Only use skills that exist in our vocabulary.
        if group.get("assessment") == "manual_review":

            evidence = resume_evidence.get(
                group["key"],
                [],
            )

            status = (
                "evidence_found"
                if evidence
                else "not_assessed"
            )

            results.append({
                "competency": group["name"],
                "level": group["level"],
                "status": status,
                "matched_skills": [],
                "possible_skills": [],
                "graph_supported_skills": [],
                "evidence": evidence,
            })

            continue
        alternatives = [
            skill
            for skill in group["any_of"]
            if skill in catalog
        ]

        if not alternatives:
            raise ValueError(
                f"No catalog skills for group '{group['key']}'."
            )

        matched = [
            skill
            for skill in alternatives
            if skill in user_skills
        ]

        supported_by_graph = [
            skill
            for skill in alternatives
            if skill in graph_skills
        ]

        results.append({
            "competency": group["name"],
            "level": group["level"],
            "status": (
                "evidenced"
                if matched
                else "not_evidenced"
            ),
            "matched_skills": matched,
            "possible_skills": alternatives,
            "graph_supported_skills": supported_by_graph,
        })

    core = [
        item
        for item in results
        if item["level"] == "core"
    ]

    assessed_core = [
        item
        for item in core
        if item["status"] in {
            "evidenced",
            "not_evidenced",
        }
    ]

    covered = sum(
        item["status"] == "evidenced"
        for item in assessed_core
    )

    evidence_found_core = sum(
        item["status"] == "evidence_found"
        for item in core
    )

    covered = sum(
        item["status"] == "evidenced"
        for item in assessed_core
    )

    return {
        "user_id": user_id,
        "career_key": career_key,
        "career_name": career.name,
        "core_competencies": len(core),
        "core_competencies_assessed": len(assessed_core),
        "core_competencies_evidenced": covered,
        "core_competencies_not_assessed": len(core) - len(assessed_core),
        "core_competencies_evidence_found": evidence_found_core,
        "competencies": results,
    }