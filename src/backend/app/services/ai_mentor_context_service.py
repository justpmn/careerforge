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

MAX_RESOURCE_LINKS = 10
MAX_RESOURCES_PER_COMPETENCY = 3


def build_learning_resources_context(
    assessment: dict[str, Any],
    competencies: list[dict],
    total_competencies: int,
) -> dict:
    """
    Build a resource-focused context using actual
    learning resources returned by the assessment.

    Never generate or guess resource URLs.
    """
    remaining_links = MAX_RESOURCE_LINKS
    resource_competencies = []

    for item in competencies:
        raw_resources = item.get("learning_resources") or []

        if not isinstance(raw_resources, list):
            raw_resources = []

        selected_resources = []

        for resource in raw_resources:
            if remaining_links <= 0:
                break

            if len(selected_resources) >= MAX_RESOURCES_PER_COMPETENCY:
                break

            if not isinstance(resource, dict):
                continue

            url = resource.get("url")
            title = resource.get("title")

            if (
                not isinstance(url, str)
                or not url.startswith(("https://", "http://"))
                or not isinstance(title, str)
                or not title.strip()
            ):
                continue

            selected_resources.append({
                "title": title,
                "provider": resource.get("provider"),
                "url": url,
                "matched_skills": resource.get(
                    "matched_skills", []
                ),
            })

            remaining_links -= 1

        resource_competencies.append({
            "competency_key": item["competency_key"],
            "competency": item["competency"],
            "level": item["level"],
            "available_resource_count": len(raw_resources),
            "learning_resources": selected_resources,
        })

    return {
        "source": "careerforge_competency_assessment",
        "focus": "learning_resources",
        "career": {
            "key": assessment["career_key"],
            "name": assessment["career_name"],
        },
        "competency_resources": resource_competencies,
        "total_competencies": total_competencies,
        "omitted_competencies": max(
            0,
            total_competencies - len(competencies),
        ),
        "resource_limit": MAX_RESOURCE_LINKS,
    }


def build_mentor_context(
    assessment: dict[str, Any],
    *,
    include_resources: bool = False,
) -> dict:
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
    if include_resources:
        return build_learning_resources_context(
            assessment=assessment,
            competencies=selected_competencies,
            total_competencies=len(competencies),
        )

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
