from sqlalchemy import select

from src.backend.app.database.session import SessionLocal
from src.backend.app.database.models.resume import Resume

from src.preprocessing.competency_evidence_extractor import (
    extract_competency_evidence,
)


USER_ID = 2


def main():

    # Quick check that basic phrase detection works.
    sample = (
        "Implemented OTP authentication. "
        "Troubleshooting network issues."
    )

    sample_result = extract_competency_evidence(sample)

    assert sample_result["authentication_security"]
    assert sample_result["debugging"]

    print("Synthetic evidence check: PASSED")

    # Retrieve the user's most recent saved resume.
    with SessionLocal() as db:
        resume = db.scalar(
            select(Resume)
            .where(
                Resume.user_id == USER_ID,
                Resume.extracted_text.is_not(None),
            )
            .order_by(
                Resume.uploaded_at.desc(),
                Resume.id.desc(),
            )
        )

        if resume is None:
            print("No saved resume found.")
            return

        resume_id = resume.id
        text = resume.extracted_text

    print("\nRESUME COMPETENCY EVIDENCE")
    print("-" * 50)
    print("Resume ID:", resume_id)

    results = extract_competency_evidence(text)

    for competency, evidence in results.items():

        print(f"\nCOMPETENCY: {competency}")

        if not evidence:
            print("No explicit evidence detected.")
            continue

        for item in evidence:
            print(
                "Matched phrase:",
                item["matched_phrase"],
            )

            print(
                "Evidence:",
                item["excerpt"],
            )

            print()


if __name__ == "__main__":
    main()