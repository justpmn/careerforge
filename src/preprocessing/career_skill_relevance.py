from pathlib import Path

import pandas as pd


DATA_PATH = Path(
    "data/processed/final_career_skills.csv"
)


def rank_career_skill_evidence(
    career_key: str,
    top_n: int = 25,
) -> pd.DataFrame:

    df = pd.read_csv(DATA_PATH)

    df["stackoverflow_frequency"] = (
        pd.to_numeric(
            df["stackoverflow_frequency"],
            errors="coerce",
        )
        .fillna(0)
        .clip(lower=0)
    )

    # Build a skill-by-career frequency matrix.
    matrix = df.pivot_table(
        index="canonical_skill",
        columns="career_key",
        values="stackoverflow_frequency",
        aggfunc="max",
        fill_value=0.0,
    )

    if career_key not in matrix.columns:
        raise ValueError(
            f"Unknown career: {career_key}"
        )

    # Retrieve the selected career's associations.
    career = df[
        df["career_key"] == career_key
    ].copy()

    # Compare frequency against other career classes.
    other_careers = matrix.drop(
        columns=[career_key]
    )

    average_other = other_careers.mean(axis=1)

    career["average_other_frequency"] = (
        career["canonical_skill"]
        .map(average_other)
        .fillna(0)
    )

    frequency = career[
        "stackoverflow_frequency"
    ]

    other_frequency = career[
        "average_other_frequency"
    ]

    career["specificity"] = (
        frequency
        / (frequency + other_frequency + 0.02)
    )

    career["evidence_score"] = (
        frequency
        * (0.7 + 0.3 * career["specificity"])
    )

    # Exclude entries with no Stack Overflow evidence
    # from automatic ranking.
    career = career[
        frequency > 0
    ].copy()

    career = career.sort_values(
        "evidence_score",
        ascending=False,
    )

    return career.head(top_n)[
        [
            "canonical_skill",
            "skill_types",
            "stackoverflow_frequency",
            "specificity",
            "evidence_score",
        ]
    ].reset_index(drop=True)