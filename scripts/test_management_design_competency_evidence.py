
from src.preprocessing.competency_evidence_extractor import (
    extract_competency_evidence,
)


TEST_CASES = {
    "ui_ux_designer": {
        "text": (
            "Conducted user research and mapped user flows. "
            "Created wireframes and interactive prototypes. "
            "Applied interaction design and performed usability testing. "
            "Maintained design systems, conducted WCAG accessibility audits, "
            "improved visual hierarchy and completed design handoff."
        ),
        "expected": [
            "user_research",
            "information_architecture",
            "wireframing",
            "prototyping",
            "interaction_design",
            "usability_testing",
            "design_systems",
            "ux_accessibility",
            "visual_design",
            "design_handoff",
        ],
    },

    "product_manager": {
        "text": (
            "Defined product strategy after customer discovery. "
            "Planned product roadmaps and feature prioritization. "
            "Gathered business requirements and coordinated "
            "stakeholder alignment. Tracked product metrics, "
            "coordinated a product launch and ran A/B testing."
        ),
        "expected": [
            "product_strategy",
            "product_discovery",
            "product_roadmap",
            "feature_prioritization",
            "requirements_analysis",
            "stakeholder_management",
            "product_metrics",
            "product_launch",
            "product_experimentation",
        ],
    },

    "it_project_manager": {
        "text": (
            "Performed project planning and scope management. "
            "Built Gantt charts, tracked project budgets and "
            "maintained a risk register. Coordinated stakeholder "
            "engagement and project delivery. Submitted project "
            "status reports, reviewed change requests and "
            "acceptance criteria, and followed Agile methodologies."
        ),
        "expected": [
            "project_planning",
            "scope_management",
            "project_scheduling",
            "budget_management",
            "project_risk_management",
            "stakeholder_management",
            "project_delivery",
            "project_communication",
            "project_change_management",
            "project_quality_management",
            "delivery_methodologies",
        ],
    },
}


def main():
    total_checks = 0
    all_domain_keys = {
        key
        for case in TEST_CASES.values()
        for key in case["expected"]
    }

    for career, case in TEST_CASES.items():
        print(f"\n{'=' * 55}")
        print(f"CAREER: {career}")
        print("=" * 55)

        result = extract_competency_evidence(case["text"])

        for competency in case["expected"]:
            matches = result.get(competency, [])

            assert matches, (
                f"{career}: Missing evidence for {competency}"
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

    # Negative control: unrelated technical experience
    # should not trigger management or UX competencies.
    unrelated_resume = (
        "Built a backend API using Python, PostgreSQL and Git."
    )

    unrelated_result = extract_competency_evidence(
        unrelated_resume
    )

    unexpected = [
        key
        for key in all_domain_keys
        if unrelated_result.get(key)
    ]

    assert not unexpected, (
        f"Unexpected domain evidence: {unexpected}"
    )

    print("\nPASS: Unrelated technical resume negative control")
    print(
        f"\nALL {total_checks} DESIGN AND MANAGEMENT "
        "EVIDENCE CHECKS PASSED"
    )


if __name__ == "__main__":
    main()

