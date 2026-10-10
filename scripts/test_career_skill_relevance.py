from src.preprocessing.career_skill_relevance import (
    rank_career_skill_evidence,
)


def main():

    for career in [
        "backend_developer",
        "frontend_developer",
        "data_engineer",
    ]:

        print(f"\n{'=' * 70}")
        print(f"CAREER: {career}")
        print("=" * 70)

        ranked = rank_career_skill_evidence(
            career_key=career,
            top_n=25,
        )

        print(
            ranked.to_string(
                index=False,
                float_format=lambda x: f"{x:.3f}",
            )
        )


if __name__ == "__main__":
    main()