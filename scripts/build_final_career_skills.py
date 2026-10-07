import pandas as pd

from src.preprocessing.paths import (
    PROCESSED_DATA_DIR,
)


VOCABULARY_PATH = (
    PROCESSED_DATA_DIR
    / "final_skill_vocabulary.csv"
)

CAREER_SKILLS_PATH = (
    PROCESSED_DATA_DIR
    / "meaningful_career_skills.csv"
)

OUTPUT_PATH = (
    PROCESSED_DATA_DIR
    / "final_career_skills.csv"
)


def main():
    vocabulary = pd.read_csv(
        VOCABULARY_PATH
    )

    career_skills = pd.read_csv(
        CAREER_SKILLS_PATH
    )

    valid_skills = set(
        vocabulary[
            "canonical_skill"
        ].dropna()
    )

    final_edges = career_skills[
        career_skills[
            "canonical_skill"
        ].isin(valid_skills)
    ].copy()

    final_edges.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "Original edges:",
        len(career_skills),
    )

    print(
        "Final edges:",
        len(final_edges),
    )

    print(
        "Removed edges:",
        len(career_skills)
        - len(final_edges),
    )

    print(
        f"\nSaved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()