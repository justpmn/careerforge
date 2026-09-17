import pandas as pd
from src.preprocessing.paths import PROCESSED_DATA_DIR


MIN_STACKOVERFLOW_COUNT = 5
MIN_STACKOVERFLOW_FREQUENCY = 0.05


def main():
    print(" Final Vocabulary Refinement")
    print("___________________________________________=")

    vocabulary_path = (PROCESSED_DATA_DIR / "skill_vocabulary.csv")
    career_skills_path = (PROCESSED_DATA_DIR / "career_skills.csv")
    aliases_path = (PROCESSED_DATA_DIR / "skill_aliases.csv")

    vocabulary = pd.read_csv(vocabulary_path)
    career_skills = pd.read_csv(career_skills_path)
    aliases = pd.read_csv(aliases_path)

    print(f"\nCandidate skills: {len(vocabulary)}")
    print(f"Raw graph edges: {len(career_skills)}")


    stackoverflow_meaningful = (
        (career_skills["source_stackoverflow"] == 1)
        & (
            career_skills["stackoverflow_count"]
            >= MIN_STACKOVERFLOW_COUNT
        )
        & (
            career_skills["stackoverflow_frequency"]
            >= MIN_STACKOVERFLOW_FREQUENCY
        )
    )
    onet_meaningful = (
        (career_skills["source_onet"] == 1)
        & (
            (career_skills["onet_direct"] == 1)
            | (career_skills["onet_related"] == 1)
        )
        & (
            (career_skills["hot_technology"] == 1)
            | (career_skills["in_demand"] == 1)
            | career_skills["onet_importance"].notna()
        )
    )
    cross_source = (
        (career_skills["source_onet"] == 1)
        & (career_skills["source_stackoverflow"] == 1)
    )

    meaningful_mask = (
        stackoverflow_meaningful
        | onet_meaningful
        | cross_source
    )

    meaningful_edges = (
        career_skills[meaningful_mask]
        .copy()
        .reset_index(drop=True)
    )

    print(
        f"Meaningful graph edges: {len(meaningful_edges)}"
    )

    career_counts = (
        meaningful_edges
        .groupby("canonical_skill")["career_key"]
        .nunique()
        .rename("career_count")
        .reset_index()
    )

    total_careers = (
        career_skills["career_key"].nunique()
    )

    career_counts["career_coverage"] = (
        career_counts["career_count"]
        / total_careers
    )

    final_vocabulary = vocabulary.merge(
        career_counts,
        on="canonical_skill",
        how="inner",
    )

    final_vocabulary = (
        final_vocabulary
        .sort_values(
            [
                "career_count",
                "canonical_skill",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )
    valid_skills = set(
        final_vocabulary["canonical_skill"]
    )

    final_aliases = (
        aliases[
            aliases["canonical_skill"].isin(
                valid_skills
            )
        ]
        .copy()
        .drop_duplicates(
            subset=["alias"]
        )
        .sort_values(
            [
                "canonical_skill",
                "alias",
            ]
        )
        .reset_index(drop=True)
    )

    final_vocabulary_path = (
        PROCESSED_DATA_DIR
        / "final_skill_vocabulary.csv"
    )

    final_aliases_path = (
        PROCESSED_DATA_DIR
        / "final_skill_aliases.csv"
    )

    meaningful_edges_path = (
        PROCESSED_DATA_DIR
        / "meaningful_career_skills.csv"
    )

    final_vocabulary.to_csv(
        final_vocabulary_path,
        index=False,
    )

    final_aliases.to_csv(
        final_aliases_path,
        index=False,
    )

    meaningful_edges.to_csv(
        meaningful_edges_path,
        index=False,
    )
    removed = vocabulary[
        ~vocabulary["canonical_skill"].isin(
            final_vocabulary["canonical_skill"]
        )
    ]

    print("\n----------------------------------------")
    print(" Refinement Results")
    print("----------------------------------------")

    print(
        f"Candidate vocabulary: {len(vocabulary)}"
    )

    print(
        f"Final vocabulary:     {len(final_vocabulary)}"
    )

    print(
        f"Removed skills:       {len(removed)}"
    )

    print(
        f"Final aliases:        {len(final_aliases)}"
    )

    print(
        f"Meaningful edges:     {len(meaningful_edges)}"
    )

    print(
        f"Career classes:       {total_careers}"
    )

    print("\nTop 20 most broadly linked skills:")

    print(
        final_vocabulary[
            [
                "canonical_skill",
                "career_count",
                "career_coverage",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )

    print("\nSample removed skills:")

    print(
        removed[
            [
                "canonical_skill",
                "categories",
            ]
        ]
        .head(30)
        .to_string(index=False)
    )

    print("\nSaved:")
    print(final_vocabulary_path)
    print(final_aliases_path)
    print(meaningful_edges_path)

    print("\n========================================")
    print(" Vocabulary refinement complete")
    print("========================================")
if __name__ == "__main__":
    main()