from typing import Any
from collections import Counter

MAX_COMPETENCIES = 15
MAX_SKILLS_PER_GROUP = 4

ACTION_PRIORITY = {
    "review_submitted_evidence": 0,
    "review_resume_evidence": 1,
    "assess_competency": 2,
    "confirm_skill_experience": 3,
    "no_immediate_action": 4,
}

def build_mentor_context(assessment: dict[str, Any]) -> dict:
    """
    Prepare CareerForge competency assessment results for the LLM.

    Args:
        assessment:
            Output returned by analyze_competency_gaps().

    Returns:
        A compact dictionary containing career information,
        competency statuses, and recommended actions.

    Raises:
        ValueError:
            If the assessment does not have the expected structure.
    """
    competencies = assessment.get("competencies")

    if not isinstance(competencies, list):
        raise ValueError(
            "Invalid assessment: competencies must be a list."
        )
    ordered_competencies = sorted(
        competencies,
        key=lambda item: (
            0 if item.get("level") == "core" else 1,
            ACTION_PRIORITY.get(
                item.get("next_action"), 99
            ),
        ),
    )
    selected_competencies = ordered_competencies[
        :MAX_COMPETENCIES
    ]

    simplified_competencies = []

    for item in selected_competencies:
        simplified_competencies.append({
            "competency_key": item["competency_key"],
            "competency": item["competency"],
            "level": item["level"],
            "status": item["status"],
            "next_action": item["next_action"],
            "matched_skills": item.get(
                "matched_skills", []
            )[:MAX_SKILLS_PER_GROUP],
            "possible_skills": item.get(
                "possible_skills", []
            )[:MAX_SKILLS_PER_GROUP],
            "graph_supported_skills": item.get(
                "graph_supported_skills", []
            )[:MAX_SKILLS_PER_GROUP],
            "submitted_evidence_count": len(
                item.get("submitted_evidence", [])
            ),

            "learning_resource_count": len(
                item.get("learning_resources", [])
            ),
        })
        status_counts = dict(
        Counter(
            item["status"]
            for item in competencies
        )
    )
        
    status_counts_by_level = {
        level: dict(
            Counter(
                item["status"]
                for item in competencies
                if item["level"] == level
            )
        )
        for level in sorted({
            item["level"]
            for item in competencies
        })
    }

    context = {
        "source": "careerforge_competency_assessment",

        "career": {
            "key": assessment["career_key"],
            "name": assessment["career_name"],
        },

        "summary": {
            "core_competencies": assessment.get(
                "core_competencies", 0
            ),
            "core_competencies_assessed": assessment.get(
                "core_competencies_assessed", 0
            ),
            "core_competencies_evidenced": assessment.get(
                "core_competencies_evidenced", 0
            ),
            "core_competencies_not_assessed": assessment.get(
                "core_competencies_not_assessed", 0
            ),
            "status_counts": status_counts,
            "status_counts_by_level": status_counts_by_level,

        },

        "competencies": simplified_competencies,
        "total_competencies": len(competencies),
        "omitted_competencies": max(
            0,
            len(competencies) - MAX_COMPETENCIES,
        ),
    }

    return context
