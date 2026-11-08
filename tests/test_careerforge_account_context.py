from types import SimpleNamespace
from unittest.mock import Mock

from src.backend.app.services import (
    careerforge_account_context_service as service,
)


def test_recorded_and_self_reported_skills_are_separate():
    db = Mock()
    db.execute.return_value.all.return_value = [
        ("Python", "resume"),
        ("React", "manual"),
        ("Git", "resume"),
    ]

    result = service._skills_context(db, user_id=7)

    assert result["recorded"] == ["Git", "Python"]
    assert result["self_reported"] == ["React"]
    assert result["recorded_total"] == 2


def test_roadmap_uses_saved_progress_and_curated_resources(
    monkeypatch,
):
    db = Mock()
    db.scalar.return_value = SimpleNamespace(id=3)
    db.scalars.return_value.all.return_value = [
        SimpleNamespace(
            skill_key="api_development",
            learned=True,
        )
    ]

    monkeypatch.setattr(
        service,
        "generate_learning_roadmap",
        lambda **kwargs: {
            "career_name": "Backend Developer",
            "steps": [{
                "competency_key": "api_development",
                "competency": "API development",
                "priority_group": "essential",
                "status": "not_evidenced",
                "next_action": "confirm_skill_experience",
                "suggested_resources": [{
                    "title": "API Course",
                    "provider": "Example Provider",
                    "url": "https://example.org/course",
                }],
            }],
        },
    )

    result = service._roadmap_context(
        db=db,
        user_id=7,
        career_key="backend_developer",
        include_resources=True,
    )

    assert result["available"] is True
    assert result["marked_learned_steps"] == 1
    assert result["steps"][0]["marked_learned"] is True
    assert result["steps"][0]["resources"][0]["url"] == (
        "https://example.org/course"
    )

def test_cv_question_prioritizes_recommendations(monkeypatch):
    from src.backend.app.services import assessment_mentor_service as mentor

    monkeypatch.setattr(
        mentor,
        "build_account_mentor_context",
        lambda **kwargs: {
            "recommendations": {
                "available": True,
                "ranking": [{
                    "career_key": "backend_developer",
                    "model_score": 0.25,
                    "documented_coverage_pct": 55.6,
                }],
            },
            "career_preferences": {
                "preferred": [],
                "avoided": [],
            },
        },
    )

    result = mentor.build_grounded_mentor_context(
        db=Mock(),
        user_id=7,
        career_key="software_engineer",
        assessment={},
        include_resources=False,
        message="Compare my Random Forest scores and skill coverage.",
    )

    assert result["focus"] == "saved_cv_recommendations"
    assert result["recommendations"]["ranking"][0][
        "career_key"
    ] == "backend_developer"
    assert "assessment" not in result