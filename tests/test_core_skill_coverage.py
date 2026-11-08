from src.backend.app.services.core_skill_coverage_service import (
    calculate_core_skill_coverage,
)


def test_core_skill_coverage():
    profile = [
        {
            "key": "backend",
            "level": "core",
            "any_of": ["Python", "Node.js"],
        },
        {
            "key": "database",
            "level": "core",
            "any_of": ["PostgreSQL", "MySQL"],
        },
        {
            "key": "architecture",
            "level": "core",
            "assessment": "manual_review",
        },
        {
            "key": "frontend",
            "level": "supporting",
            "any_of": ["React"],
        },
    ]

    result = calculate_core_skill_coverage(
        profile=profile,
        catalog={"Python", "Node.js", "PostgreSQL", "MySQL", "React"},
        recorded_skills={"Python"},
        manual_skills={"PostgreSQL"},
    )

    assert result["percentage"] == 33.3
    assert result["overall_percentage"] == 28.6
    assert result["matched_core"] == 1
    assert result["total_core"] == 3
    assert result["matched_supporting"] == 0
    assert result["total_supporting"] == 1
    assert result["self_reported_core"] == 1