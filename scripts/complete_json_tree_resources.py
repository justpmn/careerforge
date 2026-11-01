
import json
from pathlib import Path

from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / (
    "src/backend/app/resource_catalog/"
    "competency_resources.json"
)

# Format: title, provider, resource_type, URL
# Existing PostgreSQL resources are reused by URL.
SOURCES = {
    # Shared foundations
    "python": (
        "The Python Tutorial", "Python", "tutorial",
        "https://docs.python.org/3/tutorial/",
    ),
    "git": (
        "Pro Git", "Git", "book",
        "https://git-scm.com/book/en/v2",
    ),
    "docker": (
        "Docker Getting Started", "Docker", "tutorial",
        "https://docs.docker.com/get-started/introduction/index.html",
    ),
    "actions": (
        "GitHub Actions Getting Started", "GitHub", "tutorial",
        "https://docs.github.com/en/actions/get-started",
    ),
    "aws": (
        "AWS Cloud Practitioner Training", "AWS", "course",
        "https://aws.amazon.com/training/learn-about/cloud-practitioner/",
    ),
    "fastapi": (
        "FastAPI Tutorial", "FastAPI", "tutorial",
        "https://fastapi.tiangolo.com/tutorial/",
    ),
    "rest": (
        "REST APIs", "MDN Web Docs", "documentation",
        "https://developer.mozilla.org/en-US/docs/Glossary/REST",
    ),
    "pytest": (
        "Getting Started with pytest", "pytest", "tutorial",
        "https://docs.pytest.org/en/stable/getting-started.html",
    ),
    "debugging": (
        "Debugging in VS Code", "Visual Studio Code",
        "documentation",
        "https://code.visualstudio.com/docs/debugtest/debugging",
    ),

    # AI and ML Engineering
    "ml_training": (
        "Supervised Learning", "scikit-learn", "documentation",
        "https://scikit-learn.org/stable/supervised_learning.html",
    ),
    "ml_evaluation": (
        "Model Evaluation", "scikit-learn", "documentation",
        "https://scikit-learn.org/stable/modules/model_evaluation.html",
    ),
    "airflow": (
        "Apache Airflow Tutorials", "Apache Airflow", "tutorial",
        "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/",
    ),
    "pytorch": (
        "PyTorch Tutorials", "PyTorch", "tutorial",
        "https://docs.pytorch.org/tutorials/",
    ),
    "mlflow_tracking": (
        "MLflow Experiment Tracking", "MLflow", "documentation",
        "https://mlflow.org/docs/latest/tracking/",
    ),
    "mlflow_serving": (
        "MLflow Model Serving", "MLflow", "documentation",
        "https://mlflow.org/docs/latest/ml/deployment",
    ),
    "evidently": (
        "Evidently ML Monitoring", "Evidently", "documentation",
        "https://docs.evidentlyai.com/introduction",
    ),

    # Database Engineering
    "sqlbolt": (
        "SQLBolt Interactive SQL Lessons", "SQLBolt", "tutorial",
        "https://sqlbolt.com/",
    ),
    "postgres": (
        "PostgreSQL Tutorial", "PostgreSQL", "tutorial",
        "https://www.postgresql.org/docs/current/tutorial.html",
    ),
    "db_design": (
        "PostgreSQL Data Definition", "PostgreSQL", "documentation",
        "https://www.postgresql.org/docs/current/ddl.html",
    ),
    "db_optimize": (
        "Understanding PostgreSQL EXPLAIN",
        "PostgreSQL", "documentation",
        "https://www.postgresql.org/docs/current/using-explain.html",
    ),
    "db_admin": (
        "PostgreSQL Server Administration",
        "PostgreSQL", "documentation",
        "https://www.postgresql.org/docs/current/admin.html",
    ),
    "db_backup": (
        "PostgreSQL Backup and Recovery",
        "PostgreSQL", "documentation",
        "https://www.postgresql.org/docs/current/backup.html",
    ),
    "db_security": (
        "PostgreSQL Database Roles", "PostgreSQL", "documentation",
        "https://www.postgresql.org/docs/current/user-manag.html",
    ),
    "db_monitoring": (
        "Monitoring PostgreSQL Activity",
        "PostgreSQL", "documentation",
        "https://www.postgresql.org/docs/current/monitoring.html",
    ),
    "alembic": (
        "Alembic Database Migration Tutorial",
        "SQLAlchemy", "tutorial",
        "https://alembic.sqlalchemy.org/en/latest/tutorial.html",
    ),
    "mongodb": (
        "MongoDB Tutorials", "MongoDB", "tutorial",
        "https://www.mongodb.com/docs/manual/tutorial/",
    ),

    # Mobile Development
    "android_course": (
        "Android Development Training",
        "Android Developers", "course",
        "https://developer.android.com/courses",
    ),
    "kotlin": (
        "Get Started with Kotlin", "Kotlin", "tutorial",
        "https://kotlinlang.org/docs/getting-started.html",
    ),
    "android_studio": (
        "Meet Android Studio", "Android Developers",
        "documentation",
        "https://developer.android.com/studio/intro",
    ),
    "compose": (
        "Jetpack Compose Tutorial", "Android Developers",
        "tutorial",
        "https://developer.android.com/develop/ui/compose/tutorial",
    ),
    "android_platform": (
        "Android API Reference", "Android Developers",
        "documentation",
        "https://developer.android.com/reference",
    ),
    "android_network": (
        "Android Network Connectivity", "Android Developers",
        "documentation",
        "https://developer.android.com/develop/connectivity/network-ops/connecting",
    ),
    "android_room": (
        "Android Room Database", "Android Developers",
        "documentation",
        "https://developer.android.com/training/data-storage/room",
    ),
    "android_testing": (
        "Test Android Applications", "Android Developers",
        "tutorial",
        "https://developer.android.com/training/testing",
    ),
    "android_publish": (
        "Publish Your Android App", "Android Developers",
        "documentation",
        "https://developer.android.com/studio/publish",
    ),

    # Quality Assurance
    "istqb": (
        "Software Testing Foundation Syllabus",
        "ISTQB", "course",
        "https://istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0/",
    ),
    "bugs": (
        "Bug Tracking Guide", "Atlassian", "documentation",
        "https://www.atlassian.com/agile/software-development/bug-tracking",
    ),
    "postman": (
        "Getting Started with Postman", "Postman", "tutorial",
        "https://learning.postman.com/docs/getting-started/overview/",
    ),
    "k6": (
        "Get Started with k6", "Grafana", "tutorial",
        "https://grafana.com/docs/k6/latest/get-started/",
    ),

    # Software Engineering
    "design_patterns": (
        "Software Design Patterns", "Refactoring Guru",
        "tutorial",
        "https://refactoring.guru/design-patterns",
    ),
}


# Every competency gets at least one curated resource.
# This complements the canonical skill resources in PostgreSQL.
MAPPINGS = {
    "ai_ml_engineer": {
        "ml_programming": ["python"],
        "ml_training": ["ml_training", "pytorch"],
        "model_evaluation": ["ml_evaluation"],
        "pipeline_design": ["airflow"],
        "model_serving": ["mlflow_serving", "fastapi"],
        "model_monitoring": ["evidently"],
        "ml_libraries": ["pytorch"],
        "model_api_tooling": ["fastapi"],
        "ml_workflows": ["mlflow_tracking"],
        "version_control": ["git"],
        "containers": ["docker"],
        "cloud_platform": ["aws"],
        "ci_cd": ["actions"],
    },

    "database_engineer": {
        "sql": ["sqlbolt"],
        "db_platform": ["postgres"],
        "database_architecture": ["db_design"],
        "query_optimization": ["db_optimize"],
        "database_administration": ["db_admin"],
        "backup_recovery": ["db_backup"],
        "database_security": ["db_security"],
        "database_monitoring": ["db_monitoring"],
        "database_migrations": ["alembic"],
        "db_automation": ["python"],
        "nosql_db": ["mongodb"],
        "version_control": ["git"],
    },

    "mobile_developer": {
        "mobile_app_development": ["android_course"],
        "mobile_ui": ["compose"],
        "mobile_platform_integration": ["android_platform"],
        "mobile_testing": ["android_testing"],
        "mobile_languages": ["kotlin"],
        "mobile_tooling": ["android_studio"],
        "mobile_storage": ["android_room"],
        "mobile_api": ["android_network"],
        "mobile_release": ["android_publish"],
        "version_control": ["git"],
    },

    "qa_test_engineer": {
        "testing": ["pytest"],
        "test_strategy": ["istqb"],
        "defect_management": ["bugs"],
        "test_programming": ["python"],
        "debugging": ["debugging"],
        "api_testing": ["postman"],
        "performance_testing": ["k6"],
        "version_control": ["git"],
        "ci_cd": ["actions"],
    },

    "software_engineer": {
        "programming": ["python"],
        "software_design": ["design_patterns"],
        "database": ["postgres"],
        "api": ["fastapi", "rest"],
        "debugging": ["debugging"],
        "version_control": ["git"],
        "testing": ["pytest"],
        "ci_cd": ["actions"],
        "containers": ["docker"],
    },
}


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    if catalog.get("version") != 1:
        raise ValueError("Unsupported catalog version")

    resources = catalog["resources"]
    mappings = catalog["mappings"]

    # Validate all 53 IDs against the backend.
    for career_key, competency_map in MAPPINGS.items():
        expected = {
            group["key"]
            for group in CAREER_COMPETENCY_PROFILES[career_key]
        }
        actual = set(competency_map)

        if actual != expected:
            raise ValueError(
                f"{career_key}: "
                f"missing={sorted(expected - actual)}, "
                f"unknown={sorted(actual - expected)}"
            )

        for aliases in competency_map.values():
            for alias in aliases:
                if alias not in SOURCES:
                    raise ValueError(f"Unknown resource: {alias}")

    # Add any resource URL not already defined in the catalog.
    known_urls = {item["url"] for item in resources}
    resources_added = 0

    for title, provider, resource_type, url in SOURCES.values():
        if url in known_urls:
            continue

        resources.append({
            "title": title,
            "provider": provider,
            "resource_type": resource_type,
            "url": url,
            "description": (
                f"Study {title.lower()} using resources from {provider}."
            ),
        })
        known_urls.add(url)
        resources_added += 1

    # Merge career-specific mappings by career and competency.
    by_key = {
        (item["career_key"], item["competency_key"]): item
        for item in mappings
    }

    mappings_added = 0

    for career_key, competency_map in MAPPINGS.items():
        for competency_key, aliases in competency_map.items():
            urls = [SOURCES[alias][3] for alias in aliases]
            key = (career_key, competency_key)

            if key in by_key:
                item = by_key[key]
                item["urls"] = list(
                    dict.fromkeys(item["urls"] + urls)
                )
            else:
                item = {
                    "career_key": career_key,
                    "competency_key": competency_key,
                    "urls": list(dict.fromkeys(urls)),
                }
                mappings.append(item)
                by_key[key] = item
                mappings_added += 1

    # Final structural validation.
    resource_urls = [item["url"] for item in resources]

    if len(resource_urls) != len(set(resource_urls)):
        raise ValueError("Duplicate resource URL found")

    mapping_keys = [
        (item["career_key"], item["competency_key"])
        for item in mappings
    ]

    if len(mapping_keys) != len(set(mapping_keys)):
        raise ValueError("Duplicate competency mapping found")

    total = sum(len(items) for items in MAPPINGS.values())

    if total != 53:
        raise ValueError(f"Expected 53 competencies, found {total}")

    # Write after validation, using an atomic file replacement.
    temporary = CATALOG.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(CATALOG)

    print("\nJSON CAREER RESOURCE UPDATE")
    print("=" * 45)
    print(f"Careers: {len(MAPPINGS)}")
    print(f"Competencies: {total}")
    print(f"Resources added to catalog: {resources_added}")
    print(f"Mappings added: {mappings_added}")
    print(f"Total catalog mappings: {len(mappings)}")
    print("Update successful.")


if __name__ == "__main__":
    main()
