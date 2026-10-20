
from src.backend.app.database.session import SessionLocal
from src.backend.app.database.models.competency_evidence import (
    CompetencyEvidence,
)
from src.backend.app.services.competency_evidence_service import (
    create_competency_evidence,
)


USER_ID = 2
CAREER_KEY = "it_support"
COMPETENCY_KEY = "end_user_support"


def main():
    evidence_id = None

    try:
        # Test creating and saving competency evidence.
        with SessionLocal() as db:
            evidence = create_competency_evidence(
                db=db,
                user_id=USER_ID,
                career_key=CAREER_KEY,
                competency_key=COMPETENCY_KEY,
                evidence_type="experience",
                description=(
                    "Provided technical support to staff "
                    "and resolved software issues."
                ),
            )

            evidence_id = evidence.id

            assert evidence.verification_status == "self_reported"

            print("Evidence creation: PASSED")
            print("Evidence ID:", evidence_id)

        # Verify persistence using a new database session.
        with SessionLocal() as db:
            saved = db.get(CompetencyEvidence, evidence_id)

            assert saved is not None
            assert saved.user_id == USER_ID
            assert saved.competency_key == COMPETENCY_KEY
            assert saved.evidence_type == "experience"
            assert saved.verification_status == "self_reported"

            print("Database retrieval: PASSED")

        # Verify invalid competency keys are rejected.
        with SessionLocal() as db:
            try:
                create_competency_evidence(
                    db=db,
                    user_id=USER_ID,
                    career_key=CAREER_KEY,
                    competency_key="invalid_competency",
                    evidence_type="project",
                    description="Test evidence",
                )
            except ValueError:
                print("Invalid competency validation: PASSED")
            else:
                raise AssertionError(
                    "Invalid competency was accepted."
                )

        # Verify unsupported evidence types are rejected.
        with SessionLocal() as db:
            try:
                create_competency_evidence(
                    db=db,
                    user_id=USER_ID,
                    career_key=CAREER_KEY,
                    competency_key=COMPETENCY_KEY,
                    evidence_type="unknown",
                    description="Test evidence",
                )
            except ValueError:
                print("Evidence type validation: PASSED")
            else:
                raise AssertionError(
                    "Unsupported evidence type was accepted."
                )

        print("\nALL STORAGE TESTS PASSED")

    finally:
        # Remove only the record created by this test.
        if evidence_id is not None:
            with SessionLocal() as db:
                saved = db.get(CompetencyEvidence, evidence_id)

                if saved is not None:
                    db.delete(saved)
                    db.commit()

            print("Test record cleaned up.")


if __name__ == "__main__":
    main()
