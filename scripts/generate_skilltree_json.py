
import json
from pathlib import Path

from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)


OUTPUT_DIR = Path("src/frontend/src/lib/skilltrees")

# Each entry contains:
# competency key, short display title, prerequisite keys.
#
# Prerequisites indicate a suggested learning sequence.
# They do not lock skills or imply verified proficiency.

TREE_SPECS = {
    "ai_ml_engineer": [
        ("ml_programming", "ML Programming", []),
        ("version_control", "Git", []),
        ("cloud_platform", "Cloud", []),
        ("containers", "Containers", []),
        ("ml_libraries", "ML Frameworks",
         ["ml_programming"]),
        ("ml_training", "Model Training",
         ["ml_programming", "ml_libraries"]),
        ("pipeline_design", "ML Pipelines",
         ["ml_programming"]),
        ("model_evaluation", "Model Evaluation",
         ["ml_training"]),
        ("model_api_tooling", "API Frameworks",
         ["ml_programming"]),
        ("ml_workflows", "MLOps",
         ["ml_training", "version_control"]),
        ("model_serving", "Model Serving",
         ["ml_training", "model_api_tooling"]),
        ("ci_cd", "CI/CD",
         ["version_control", "containers"]),
        ("model_monitoring", "Model Monitoring",
         ["model_serving", "model_evaluation"]),
    ],

    "database_engineer": [
        ("sql", "SQL", []),
        ("db_platform", "Database Platforms", []),
        ("version_control", "Git", []),
        ("nosql_db", "NoSQL", []),
        ("db_automation", "DB Scripting",
         ["sql"]),
        ("database_architecture", "Database Design",
         ["sql", "db_platform"]),
        ("database_administration", "DB Administration",
         ["db_platform"]),
        ("query_optimization", "Query Optimization",
         ["sql", "database_architecture"]),
        ("database_migrations", "DB Migrations",
         ["database_architecture", "version_control"]),
        ("database_security", "Database Security",
         ["database_administration"]),
        ("backup_recovery", "Backup and Recovery",
         ["database_administration"]),
        ("database_monitoring", "DB Monitoring",
         ["database_administration", "query_optimization"]),
    ],

    "mobile_developer": [
        ("mobile_languages", "Mobile Programming", []),
        ("version_control", "Git", []),
        ("mobile_tooling", "Mobile Dev Tools",
         ["mobile_languages"]),
        ("mobile_app_development", "App Development",
         ["mobile_languages", "mobile_tooling"]),
        ("mobile_ui", "Mobile UI",
         ["mobile_app_development"]),
        ("mobile_platform_integration", "Platform APIs",
         ["mobile_app_development"]),
        ("mobile_storage", "Mobile Storage",
         ["mobile_app_development"]),
        ("mobile_api", "API Integration",
         ["mobile_app_development"]),
        ("mobile_testing", "Mobile Testing",
         ["mobile_ui", "mobile_platform_integration", "mobile_api"]),
        ("mobile_release", "App Distribution",
         ["mobile_testing", "version_control"]),
    ],

    "qa_test_engineer": [
        ("test_programming", "Test Programming", []),
        ("version_control", "Git", []),
        ("test_strategy", "Test Strategy", []),
        ("debugging", "Debugging",
         ["test_programming"]),
        ("testing", "Automated Testing",
         ["test_strategy", "test_programming"]),
        ("defect_management", "Defect Management",
         ["test_strategy", "debugging"]),
        ("api_testing", "API Testing",
         ["testing"]),
        ("performance_testing", "Performance Testing",
         ["testing"]),
        ("ci_cd", "CI/CD",
         ["version_control", "testing"]),
    ],

    "software_engineer": [
        ("programming", "Programming", []),
        ("version_control", "Git", []),
        ("software_design", "Software Design",
         ["programming"]),
        ("database", "Databases",
         ["programming"]),
        ("debugging", "Debugging",
         ["programming"]),
        ("api", "API Development",
         ["programming", "database"]),
        ("testing", "Automated Testing",
         ["software_design", "debugging"]),
        ("containers", "Containers",
         ["api"]),
        ("ci_cd", "CI/CD",
         ["version_control", "testing", "containers"]),
    ],
}


def validate_tree(career_key, spec):
    profile = CAREER_COMPETENCY_PROFILES[career_key]

    expected = {item["key"] for item in profile}
    actual = [item[0] for item in spec]

    if len(actual) != len(set(actual)):
        raise ValueError(f"Duplicate nodes in {career_key}")

    actual_set = set(actual)

    if actual_set != expected:
        raise ValueError(
            f"{career_key}\n"
            f"Missing: {sorted(expected - actual_set)}\n"
            f"Unknown: {sorted(actual_set - expected)}"
        )

    dependencies = {
        key: requires
        for key, _, requires in spec
    }

    for key, requires in dependencies.items():
        for dependency in requires:
            if dependency not in actual_set:
                raise ValueError(
                    f"{career_key}: {key} references "
                    f"unknown dependency {dependency}"
                )

    visited = set()
    visiting = set()

    def visit(key):
        if key in visiting:
            raise ValueError(
                f"Circular dependency in {career_key}: {key}"
            )

        if key in visited:
            return

        visiting.add(key)

        for dependency in dependencies[key]:
            visit(dependency)

        visiting.remove(key)
        visited.add(key)

    for key in actual:
        visit(key)


def build_template(career_key, spec):
    profile_by_key = {
        item["key"]: item
        for item in CAREER_COMPETENCY_PROFILES[career_key]
    }

    nodes = []

    for key, title, requires in spec:
        competency = profile_by_key[key]

        node = {
            "id": key,
            "title": title,
            "requires": requires,
        }

        # Use the backend's canonical skill alternatives.
        # This keeps the visual tree consistent with CV evidence.
        aliases = [
            value
            for value in (competency.get("any_of") or [])
            if isinstance(value, str)
        ]

        if aliases:
            node["skillAliases"] = sorted(set(aliases))

        nodes.append(node)

    return {
        "version": 1,
        "nodes": nodes,
    }


def main():
    # Validate everything before writing any JSON files.
    for career_key, spec in TREE_SPECS.items():
        validate_tree(career_key, spec)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for career_key, spec in TREE_SPECS.items():
        template = build_template(career_key, spec)

        output = OUTPUT_DIR / f"{career_key}.json"

        output.write_text(
            json.dumps(template, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        print(
            f"CREATED: {output.name} "
            f"({len(template['nodes'])} nodes)"
        )

    print("\nAll five career trees generated successfully.")


if __name__ == "__main__":
    main()
