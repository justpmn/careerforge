
from copy import deepcopy
import json

import pytest

from src.backend.app.services.ai_mentor_context_service import (
    MAX_COMPETENCIES,
    MAX_SKILLS_PER_GROUP,
    build_mentor_context,
)


def make_competency(
    key,
    level="supporting",
    status="not_evidenced",
    action="confirm_skill_experience",
    **extra,
):
    item = {
        "competency_key": key,
        "competency": key.replace("_", " ").title(),
        "level": level,
        "status": status,
        "next_action": action,
        "matched_skills": [],
        "possible_skills": [],
        "graph_supported_skills": [],
        "submitted_evidence": [],
        "learning_resources": [],
    }

    item.update(extra)
    return item


def make_assessment(competencies):
    core = [
        item for item in competencies
        if item["level"] == "core"
    ]

    return {
        "career_key": "data_scientist",
        "career_name": "Data Scientist",
        "core_competencies": len(core),
        "core_competencies_assessed": sum(
            item["status"] != "not_assessed"
            for item in core
        ),
        "core_competencies_evidenced": sum(
            item["status"] == "evidenced"
            for item in core
        ),
        "core_competencies_not_assessed": sum(
            item["status"] == "not_assessed"
            for item in core
        ),
        "competencies": competencies,
    }


def test_competency_status_counts():
    competencies = (
        [
            make_competency(
                f"evidenced_{i}",
                "core",
                "evidenced",
                "no_immediate_action",
            )
            for i in range(2)
        ]
        + [
            make_competency(
                f"core_unassessed_{i}",
                "core",
                "not_assessed",
                "assess_competency",
            )
            for i in range(5)
        ]
        + [
            make_competency(
                "communication",
                "supporting",
                "not_assessed",
                "assess_competency",
            )
        ]
        + [
            make_competency(f"supporting_gap_{i}")
            for i in range(4)
        ]
    )

    context = build_mentor_context(
        make_assessment(competencies)
    )

    summary = context["summary"]

    assert context["career"]["name"] == "Data Scientist"
    assert context["total_competencies"] == 12

    assert summary["status_counts"] == {
        "evidenced": 2,
        "not_assessed": 6,
        "not_evidenced": 4,
    }

    assert summary["status_counts_by_level"] == {
        "core": {
            "evidenced": 2,
            "not_assessed": 5,
        },
        "supporting": {
            "not_assessed": 1,
            "not_evidenced": 4,
        },
    }

    assert summary["core_competencies"] == 7
    assert summary["core_competencies_evidenced"] == 2


def test_empty_assessment():
    context = build_mentor_context(
        make_assessment([])
    )

    assert context["competencies"] == []
    assert context["total_competencies"] == 0
    assert context["omitted_competencies"] == 0
    assert context["summary"]["status_counts"] == {}
    assert context["summary"]["status_counts_by_level"] == {}


def test_core_competencies_prioritized():
    competencies = [
        make_competency(
            "supporting_review",
            "supporting",
            "not_assessed",
            "review_submitted_evidence",
        ),
        make_competency(
            "core_completed",
            "core",
            "evidenced",
            "no_immediate_action",
        ),
        make_competency(
            "core_assess",
            "core",
            "not_assessed",
            "assess_competency",
        ),
        make_competency(
            "core_review",
            "core",
            "not_assessed",
            "review_submitted_evidence",
        ),
    ]

    context = build_mentor_context(
        make_assessment(competencies)
    )

    keys = [
        item["competency_key"]
        for item in context["competencies"]
    ]

    assert keys == [
        "core_review",
        "core_assess",
        "core_completed",
        "supporting_review",
    ]


def test_competency_limit_and_omissions():
    competencies = [
        make_competency(f"supporting_{i}")
        for i in range(16)
    ]

    competencies.append(
        make_competency(
            "completed_skill",
            status="evidenced",
            action="no_immediate_action",
        )
    )

    context = build_mentor_context(
        make_assessment(competencies)
    )

    assert len(context["competencies"]) == MAX_COMPETENCIES
    assert context["total_competencies"] == 17
    assert context["omitted_competencies"] == 2

    assert context["summary"]["status_counts"] == {
        "not_evidenced": 16,
        "evidenced": 1,
    }


def test_skill_limits_and_resource_counts():
    skills = [
        f"Skill {i}"
        for i in range(8)
    ]

    item = make_competency(
        "python",
        "core",
        "evidenced",
        "no_immediate_action",
        matched_skills=skills,
        possible_skills=skills,
        graph_supported_skills=skills,
        submitted_evidence=[{"id": 1}, {"id": 2}],
        learning_resources=[{"id": 1}, {"id": 2}],
    )

    context = build_mentor_context(
        make_assessment([item])
    )

    result = context["competencies"][0]

    assert len(result["matched_skills"]) == MAX_SKILLS_PER_GROUP
    assert len(result["possible_skills"]) == MAX_SKILLS_PER_GROUP
    assert len(result["graph_supported_skills"]) == MAX_SKILLS_PER_GROUP

    assert result["submitted_evidence_count"] == 2
    assert result["learning_resource_count"] == 2


def test_sensitive_evidence_is_not_exposed():
    item = make_competency(
        "python",
        "core",
        "evidenced",
        "no_immediate_action",
        submitted_evidence=[
            {"content": "PRIVATE_EVIDENCE_CONTENT"}
        ],
        learning_resources=[
            {"url": "PRIVATE_RESOURCE_URL"}
        ],
        resume_evidence="PRIVATE_RESUME_CONTENT",
    )

    context = build_mentor_context(
        make_assessment([item])
    )

    serialized = json.dumps(context)

    assert "PRIVATE_EVIDENCE_CONTENT" not in serialized
    assert "PRIVATE_RESOURCE_URL" not in serialized
    assert "PRIVATE_RESUME_CONTENT" not in serialized

    result = context["competencies"][0]

    assert result["submitted_evidence_count"] == 1
    assert result["learning_resource_count"] == 1


def test_assessment_is_not_modified():
    assessment = make_assessment([
        make_competency(
            "python",
            "core",
            "evidenced",
            "no_immediate_action",
        )
    ])

    original = deepcopy(assessment)

    build_mentor_context(assessment)

    assert assessment == original


@pytest.mark.parametrize(
    "invalid_competencies",
    [
        None,
        {},
        "invalid",
    ],
)
def test_invalid_assessment_rejected(invalid_competencies):
    assessment = make_assessment([])
    assessment["competencies"] = invalid_competencies

    with pytest.raises(ValueError):
        build_mentor_context(assessment)
