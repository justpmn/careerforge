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
from src.backend.app.database.models.competency_evidence import (CompetencyEvidence)
from src.backend.app.services.learning_resource_service import (get_resources_for_skills)


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
        
    # Retrieve previously submitted competency evidence.
    submitted_records = db.scalars(
        select(CompetencyEvidence)
        .where(
            CompetencyEvidence.user_id == user_id,
            CompetencyEvidence.career_id == career.id,
        )
        .order_by(
            CompetencyEvidence.created_at.desc(),
            CompetencyEvidence.id.desc(),
        )
    ).all()

    submitted_evidence = {}

    for record in submitted_records:
        submitted_evidence.setdefault(
            record.competency_key,
            [],
        ).append({
            "id": record.id,
            "evidence_type": record.evidence_type,
            "description": record.description,
            "verification_status": record.verification_status,
        })


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
                "competency_key": group["key"],
                "competency": group["name"],
                "level": group["level"],
                "status": status,
                "matched_skills": [],
                "possible_skills": [],
                "graph_supported_skills": [],
                "evidence": evidence,
                "submitted_evidence": submitted_evidence.get(
                    group["key"],
                    [],
                ),
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
            "competency_key": group["key"],
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
            "submitted_evidence": submitted_evidence.get(
                group["key"],
                [],
            ),
        })
    
    for item in results:

        if item["status"] == "evidenced":
            next_action = "no_immediate_action"

        elif item["submitted_evidence"]:
            next_action = "review_submitted_evidence"

        elif item["status"] == "evidence_found":
            next_action = "review_resume_evidence"

        elif item["status"] == "not_assessed":
            next_action = "assess_competency"

        else:
            next_action = "confirm_skill_experience"

        item["next_action"] = next_action


    # Collect skills for competencies that may benefit
    # from optional learning resources.
    resource_skill_names = set()

    for item in results:
        if item["next_action"] == "confirm_skill_experience":
            resource_skill_names.update(
                item["possible_skills"]
            )

    # Retrieve matching resources in one database query.
    available_resources = get_resources_for_skills(
        db,
        list(resource_skill_names),
    )

    # Associate resources with relevant competencies.
    for item in results:
        item["learning_resources"] = []

        if item["next_action"] != "confirm_skill_experience":
            continue

        possible_skills = set(item["possible_skills"])

        item["learning_resources"] = [
            resource
            for resource in available_resources
            if possible_skills.intersection(
                resource["matched_skills"]
            )
        ]

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