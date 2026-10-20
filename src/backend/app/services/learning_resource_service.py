
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.learning_resource import ( LearningResource)
from src.backend.app.database.models.learning_resource_skill import (LearningResourceSkill)



# Resources suitable for multiple career paths.
COMMON_COMPETENCY_RESOURCE_URLS = {
    "ci_cd": [
        "https://docs.github.com/en/actions/get-started",
    ],
}


# Resources selected for specific career-competency pairs.
CAREER_COMPETENCY_RESOURCE_URLS = {
    ("backend_developer", "testing"): [
        "https://docs.pytest.org/en/stable/getting-started.html",
    ],
    
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


def get_resources_for_skills(
    db: Session,
    skill_names: list[str],
) -> list[dict]:

    # Remove duplicate skill names.
    skill_names = sorted(set(skill_names))

    if not skill_names:
        return []

    # Retrieve resources associated with canonical skills.
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
        .where(Skill.name.in_(skill_names))
        .order_by(
            LearningResource.title,
            Skill.name,
        )
    ).all()

    # Group results so a resource linked to several
    # skills appears only once.
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

    if not competency_keys:
        return {}

    # Resolve resources for this specific career.
    resource_urls = {}

    for key in competency_keys:
        resource_urls[key] = CAREER_COMPETENCY_RESOURCE_URLS.get(
            (career_key, key),
            COMMON_COMPETENCY_RESOURCE_URLS.get(key, []),
        )

    requested_urls = {
        url
        for urls in resource_urls.values()
        for url in urls
    }

    results = {
        key: []
        for key in competency_keys
    }

    if not requested_urls:
        return results

    # Fetch the required resources in one query.
    resources = db.scalars(
        select(LearningResource)
        .where(
            LearningResource.url.in_(requested_urls)
        )
    ).all()

    resources_by_url = {
        resource.url: resource
        for resource in resources
    }

    missing_urls = requested_urls - resources_by_url.keys()

    if missing_urls:
        raise ValueError(
            f"Competency resources not found: "
            f"{sorted(missing_urls)}"
        )

    for key in competency_keys:
        for url in resource_urls[key]:
            resource = resources_by_url[url]

            results[key].append({
                "id": resource.id,
                "title": resource.title,
                "provider": resource.provider,
                "resource_type": resource.resource_type,
                "url": resource.url,
                "description": resource.description,
                "matched_competency": key,
                "matched_skills": [],
            })

    return results
