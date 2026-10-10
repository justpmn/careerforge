from src.backend.app.database.session import SessionLocal

from src.backend.app.services.competency_gap_service import (
    analyze_competency_gaps,
)


def main():
    # Run the competency-gap analysis.
    with SessionLocal() as db:
        result = analyze_competency_gaps(
            db=db,
            user_id=2,
            career_key="backend_developer",
        )

    # Display the overall results.
    print("\nBACKEND DEVELOPER COMPETENCY ANALYSIS")
    print("-" * 45)

    print(
        "Core competencies evidenced:",
        result["core_competencies_evidenced"],
        "/",
        result["core_competencies_assessed"],
        "assessed",
    )

    print(
        "Core competencies not fully assessed:",
        result["core_competencies_not_assessed"],
    )

    print(
        "Core competencies with resume evidence:",
        result["core_competencies_evidence_found"],
    )

    # Display each competency and its evidence.
    for item in result["competencies"]:

        print(
            f"\n{item['competency']} "
            f"[{item['level']}]"
        )

        print("Status:", item["status"])

        if item["status"] == "evidence_found":

            for evidence in item["evidence"]:
                print(
                    "Matched phrase:",
                    evidence["matched_phrase"],
                )

                print(
                    "Excerpt:",
                    evidence["excerpt"],
                )

        elif item["status"] == "not_assessed":
            print(
                "Assessment not yet implemented."
            )

        elif item["matched_skills"]:
            print(
                "Matched:",
                ", ".join(item["matched_skills"]),
            )

        else:
            print(
                "Possible learning options:",
                ", ".join(item["possible_skills"]),
            )


if __name__ == "__main__":
    main()