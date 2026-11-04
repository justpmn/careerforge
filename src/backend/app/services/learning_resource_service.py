import json
from functools import lru_cache
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.learning_resource import (LearningResource)
from src.backend.app.database.models.learning_resource_skill import (LearningResourceSkill)
from src.backend.app.database.models.competency_resource_link import (CompetencyResourceLink)

CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "resource_catalog"
    / "competency_resources.json"
)

COMMON_COMPETENCY_RESOURCE_URLS = {
    "ci_cd": [
        "https://docs.github.com/en/actions/get-started",
    ],
}


CAREER_COMPETENCY_RESOURCE_URLS = {
    ("backend_developer", "testing"): [
        "https://docs.pytest.org/en/stable/getting-started.html",
        "https://vitest.dev/guide/",
    ],
    ("backend_developer", "debugging"): [
        "https://code.visualstudio.com/docs/debugtest/debugging",
    ],
    ("software_engineer", "debugging"): [
        "https://code.visualstudio.com/docs/debugtest/debugging",
    ],
    ("qa_test_engineer", "debugging"): [
        "https://code.visualstudio.com/docs/debugtest/debugging",
    ],
    ("frontend_developer", "testing"): [
        "https://vitest.dev/guide/",
    ],
    ("full_stack_developer", "testing"): [
        "https://vitest.dev/guide/",
    ],
    ("qa_test_engineer", "testing"): [
        "https://playwright.dev/docs/intro",
    ],
    ("qa_test_engineer", "api_testing"): [
        (
            "https://learning.postman.com/docs/"
            "tests-and-scripts/write-scripts/test-scripts"
        ),
    ],
    ("qa_test_engineer", "performance_testing"): [
        (
            "https://grafana.com/docs/k6/latest/"
            "get-started/write-your-first-test/"
        ),
    ],
}


@lru_cache(maxsize=1)
def load_competency_resource_mappings(
) -> dict[tuple[str, str], list[str]]:
    """
    Load career and competency resource mappings
    from the JSON catalog.
    """

    with CATALOG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        catalog = json.load(file)

    if catalog.get("version") != 1:
        raise ValueError(
            "Unsupported competency resource catalog version."
        )

    mappings = {}

    for item in catalog["mappings"]:
        key = (
            item["career_key"],
            item["competency_key"],
        )

        if key in mappings:
            raise ValueError(
                f"Duplicate competency resource mapping: {key}"
            )

        mappings[key] = item["urls"]

    return mappings


def get_resources_for_skills(
    db: Session,
    skill_names: list[str],
) -> list[dict]:
    """
    Retrieve resources linked to canonical skills.
    """

    skill_names = sorted(set(skill_names))

    if not skill_names:
        return []

    rows = db.execute(
        select(
            LearningResource,
            Skill.name,
        )
        .join(
            LearningResourceSkill,
            LearningResourceSkill.learning_resource_id
            == LearningResource.id,
        )
        .join(
            Skill,
            Skill.id == LearningResourceSkill.skill_id,
        )
        .where(
            Skill.name.in_(skill_names),
            LearningResource.archived_at.is_(None),
            )
        .order_by(
            LearningResource.title,
            Skill.name,
        )
    ).all()

    resources = {}

    for resource, skill_name in rows:
        if resource.id not in resources:
            resources[resource.id] = {
                "id": resource.id,
                "title": resource.title,
                "provider": resource.provider,
                "resource_type": resource.resource_type,
                "url": resource.url,
                "description": resource.description,
                "matched_skills": [],
            }

        resources[resource.id][
            "matched_skills"
        ].append(skill_name)

    return list(resources.values())



def get_resources_for_competencies(
    db: Session,
    competency_keys: list[str],
    career_key: str,
) -> dict[str, list[dict]]:
    competency_keys = sorted(set(competency_keys))

    results = {
        key: []
        for key in competency_keys
    }

    if not competency_keys:
        return results

    rows = db.execute(
        select(
            CompetencyResourceLink.competency_key,
            LearningResource,
        )
        .join(
            LearningResource,
            LearningResource.id
            == CompetencyResourceLink.resource_id,
        )
        .where(
            CompetencyResourceLink.career_key == career_key,
            CompetencyResourceLink.competency_key.in_(competency_keys),
            LearningResource.archived_at.is_(None),
        )
        .order_by(
            CompetencyResourceLink.competency_key,
            LearningResource.title,
            LearningResource.id,
        )
    ).all()

    for competency_key, resource in rows:
        results[competency_key].append({
            "id": resource.id,
            "title": resource.title,
            "provider": resource.provider,
            "resource_type": resource.resource_type,
            "url": resource.url,
            "description": resource.description,
            "matched_competency": competency_key,
            "matched_skills": [],
        })

    return results
