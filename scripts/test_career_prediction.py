from src.recommendation.predictor import (
    CareerRecommender,
)
def main():
    print("=" * 45)
    print("CareerForge Career Prediction Test")
    print("=" * 45)
    recommender = CareerRecommender()
    test_skills = [
        "Python",
        "PostgreSQL",
        "SQL",
        "Docker",
        "Git",
        "FastAPI",
    ]

    print(
        "\nUser skills:",
        test_skills,
    )

    recommendations = recommender.predict(
        test_skills,
        top_k=3,
    )
    print("\nTop career recommendations:")

    for recommendation in recommendations:
        print(
            f"{recommendation['rank']}. "
            f"{recommendation['career_key']} "
            f"({recommendation['score']:.4f})"
        )
if __name__ == "__main__":
    main()