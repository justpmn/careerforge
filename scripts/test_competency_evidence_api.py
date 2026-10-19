
from fastapi.testclient import TestClient

from src.backend.app.main import app
from src.backend.app.database.session import SessionLocal
from src.backend.app.database.models.competency_evidence import (
    CompetencyEvidence,
)


client = TestClient(app)

URL = "/api/users/2/careers/it_support/competency-evidence"


def main():
    evidence_id = None

    try:
        # Test a valid evidence submission.
        response = client.post(
            URL,
            json={
                "competency_key": "end_user_support",
                "evidence_type": "experience",
                "description": (
                    "Provided IT support and resolved "
                    "software problems for staff."
                ),
            },
        )

        assert response.status_code == 201, response.text

        data = response.json()
        evidence_id = data["id"]

        assert data["competency_key"] == "end_user_support"
        assert data["verification_status"] == "self_reported"

        print("Valid POST request: PASSED")

        # Confirm the record exists in PostgreSQL.
        with SessionLocal() as db:
            saved = db.get(CompetencyEvidence, evidence_id)

            assert saved is not None
            assert saved.description == data["description"]

        print("Database persistence: PASSED")
        
        # Verify evidence can be retrieved through GET.
        response = client.get(URL)

        assert response.status_code == 200, response.text

        result = response.json()

        assert result["user_id"] == 2
        assert result["career_key"] == "it_support"

        assert any(
            item["id"] == evidence_id
            and item["competency_key"] == "end_user_support"
            and item["verification_status"] == "self_reported"
            for item in result["evidence"]
        )

        print("Evidence GET retrieval: PASSED")


        # Invalid competency key should be rejected.
        response = client.post(
            URL,
            json={
                "competency_key": "invalid_competency",
                "evidence_type": "project",
                "description": "Test project",
            },
        )

        assert response.status_code == 400, response.text

        print("Invalid competency: PASSED")

        # Invalid evidence type should be rejected.
        response = client.post(
            URL,
            json={
                "competency_key": "end_user_support",
                "evidence_type": "unknown",
                "description": "Test evidence",
            },
        )

        assert response.status_code == 422, response.text

        print("Invalid evidence type: PASSED")

        print("\nALL COMPETENCY EVIDENCE API TESTS PASSED")

    finally:
        # Remove only the test record we created.
        if evidence_id is not None:
            with SessionLocal() as db:
                saved = db.get(CompetencyEvidence, evidence_id)

                if saved is not None:
                    db.delete(saved)
                    db.commit()

            print("Test record cleaned up.")


if __name__ == "__main__":
    main()
