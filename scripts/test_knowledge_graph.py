from src.backend.app.database.session import SessionLocal

from src.backend.app.services.knowledge_graph_service import (
    compare_user_career_skills,
)


def main():
    with SessionLocal() as db:
        result = compare_user_career_skills(
            db=db,
            user_id=2,
            career_key="backend_developer",
        )

    print("\nKNOWLEDGE GRAPH ANALYSIS")
    print("------------------------")

    print("Career:", result["career_name"])
    print("Total career skills:", result["total_career_skills"])
    print("Matched:", result["matched_count"])
    print("Potential gaps:", result["potential_gap_count"])

    print("\nMATCHED SKILLS")
    for skill in result["matched_skills"]:
        print(" +", skill)

    print("\nFIRST 15 POTENTIAL GAPS")
    for skill in result["potential_gaps"][:15]:
        print(" -", skill)


if __name__ == "__main__":
    main()