
from src.preprocessing.competency_evidence_extractor import (
    extract_competency_evidence,
)


TEST_CASES = {
    "data_scientist": {
        "text": (
            "Performed hypothesis testing and exploratory data analysis. "
            "Completed data cleaning and feature engineering. "
            "Conducted model training using GridSearchCV, "
            "model evaluation and cross-validation. "
            "Presented findings to stakeholders."
        ),
        "expected": [
            "statistics_inference",
            "exploratory_analysis",
            "data_preparation",
            "ml_training",
            "model_evaluation",
            "data_communication",
        ],
    },

    "ai_ml_engineer": {
        "text": (
            "Conducted model training and model evaluation. "
            "Deployed a machine learning model through an inference API. "
            "Implemented model monitoring for data drift "
            "and experiment tracking with MLflow."
        ),
        "expected": [
            "ml_training",
            "model_evaluation",
            "model_serving",
            "model_monitoring",
            "ml_workflows",
        ],
    },

    "data_business_analyst": {
        "text": (
            "Performed data analysis and requirements elicitation. "
            "Built interactive dashboards and tracked KPIs. "
            "Presented insights to stakeholders."
        ),
        "expected": [
            "analysis_interpretation",
            "requirements_analysis",
            "reporting_dashboards",
            "business_metrics",
            "data_communication",
        ],
    },

    "database_engineer": {
        "text": (
            "Performed database design and query optimization. "
            "Managed database administration, database backups, "
            "database access control, database monitoring "
            "and database migrations."
        ),
        "expected": [
            "database_architecture",
            "query_optimization",
            "database_administration",
            "backup_recovery",
            "database_security",
            "database_monitoring",
            "database_migrations",
        ],
    },
}


def main():
    total_checks = 0

    for career, case in TEST_CASES.items():
        print(f"\n{'=' * 55}")
        print(f"CAREER: {career}")
        print("=" * 55)

        result = extract_competency_evidence(
            case["text"]
        )

        for competency in case["expected"]:
            matches = result.get(competency, [])

            assert matches, (
                f"{career}: Missing evidence "
                f"for {competency}"
            )

            print(
                f"PASS: {competency} "
                f"-> {matches[0]['matched_phrase']}"
            )

            total_checks += 1

        print(
            f"\n{career}: "
            f"{len(case['expected'])} checks passed"
        )

    print(
        f"\nALL {total_checks} DATA AND AI "
        f"EVIDENCE CHECKS PASSED"
    )


if __name__ == "__main__":
    main()
