
from src.backend.app.database.session import SessionLocal
from src.backend.app.database.models.competency_evidence import (
    CompetencyEvidence,
)
from src.backend.app.services.competency_evidence_service import (
    create_competency_evidence,
)
from src.backend.app.services.competency_gap_service import (
    analyze_competency_gaps,
)


USER_ID = 2
CAREER_KEY = "it_support"
COMPETENCY_KEY = "end_user_support"


def main():
    evidence_id = None

    try:
        with SessionLocal() as db:

            # Capture existing assessment results.
            before = analyze_competency_gaps(
                db=db,
                user_id=USER_ID,
                career_key=CAREER_KEY,
            )

            # Submit temporary test evidence.
            record = create_competency_evidence(
                db=db,
                user_id=USER_ID,
                career_key=CAREER_KEY,
                competency_key=COMPETENCY_KEY,
                evidence_type="experience",
                description=(
                    "Provided technical support to users "
                    "and resolved software issues."
                ),
            )

            evidence_id = record.id

            # Re-run the competency assessment.
            after = analyze_competency_gaps(
                db=db,
                user_id=USER_ID,
                career_key=CAREER_KEY,
            )

            # Find our target competency.
            competency = next(
                item
                for item in after["competencies"]
                if item["competency_key"] == COMPETENCY_KEY
            )

            submitted = competency["submitted_evidence"]

            # Confirm our saved evidence appears.
            assert any(
                item["id"] == evidence_id
                and item["verification_status"] == "self_reported"
                for item in submitted
            )

            print("Submitted evidence integration: PASSED")

            # Confirm all competency responses expose the field.
            assert all(
                "submitted_evidence" in item
                for item in after["competencies"]
            )

            print("Response structure: PASSED")

            # Self-reported evidence must not alter assessment status.
            before_statuses = {
                item["competency_key"]: item["status"]
                for item in before["competencies"]
            }

            after_statuses = {
                item["competency_key"]: item["status"]
                for item in after["competencies"]
            }

            assert before_statuses == after_statuses

            print("Assessment statuses unchanged: PASSED")

            # Summary counts must also remain unchanged.
            summary_keys = [
                "core_competencies",
                "core_competencies_assessed",
                "core_competencies_evidenced",
                "core_competencies_not_assessed",
                "core_competencies_evidence_found",
            ]

            for key in summary_keys:
                assert before[key] == after[key]

            print("Assessment summary unchanged: PASSED")

            print("\nALL INTEGRATION TESTS PASSED")

    finally:
        # Delete only the temporary test record.
        if evidence_id is not None:
            with SessionLocal() as db:
                saved = db.get(CompetencyEvidence, evidence_id)

                if saved is not None:
                    db.delete(saved)
                    db.commit()

            print("Test evidence cleaned up.")


if __name__ == "__main__":
    main()
