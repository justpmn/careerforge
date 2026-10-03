from src.recommendation.service import (
    CareerRecommendationService,
)


def main():
    print("=" * 50)
    print("CareerForge Recommendation Service Test")
    print("=" * 50)

    resume_text = """
    Software developer with experience building
    backend applications using Python and FastAPI.

    Skilled in PostgreSQL, SQL, Docker and Git.
    Experience developing REST APIs and working
    with database-driven applications.
    """

    service = CareerRecommendationService()

    result = service.recommend_from_text(
        resume_text,
        top_k=3,
    )

    print("\nExtracted skills:")

    for skill in result["extracted_skills"]:
        print("-", skill)

    print("\nSkills used by Random Forest:")

    for skill in result["model_skills"]:
        print("-", skill)

    print("\nExtracted but not used by RF:")

    for skill in result["ignored_skills"]:
        print("-", skill)

    print("\nTop career recommendations:")

    for recommendation in result[
        "recommendations"
    ]:
        print(
            f"{recommendation['rank']}. "
            f"{recommendation['career_key']} "
            f"({recommendation['score']:.4f})"
        )


if __name__ == "__main__":
    main()