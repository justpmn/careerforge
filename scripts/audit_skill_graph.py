import pandas as pd

from src.preprocessing.paths import PROCESSED_DATA_DIR


def main():
    career_skills_path = (
        PROCESSED_DATA_DIR / "career_skills.csv"
    )

    aliases_path = (
        PROCESSED_DATA_DIR / "skill_aliases.csv"
    )

    career_skills = pd.read_csv(
        career_skills_path
    )

    aliases = pd.read_csv(
        aliases_path
    )

    # Count each possible combination of source flags.
    source_counts = (
        career_skills
        .groupby(
            [
                "source_onet",
                "source_stackoverflow",
            ]
        )
        .size()
    )

    both_sources = int(
        source_counts.get((1, 1), 0)
    )

    onet_only = int(
        source_counts.get((1, 0), 0)
    )

    stackoverflow_only = int(
        source_counts.get((0, 1), 0)
    )

    neither_source = int(
        source_counts.get((0, 0), 0)
    )

    classified_edges = (
        both_sources
        + onet_only
        + stackoverflow_only
        + neither_source
    )

    print("\nSkill Graph Audit")
    print("------------------------------")

    print(
        f"Both sources:          {both_sources}"
    )

    print(
        f"O*NET only:            {onet_only}"
    )

    print(
        f"Stack Overflow only:   {stackoverflow_only}"
    )

    print(
        f"Neither source:        {neither_source}"
    )

    print(
        f"\nTotal graph edges:     {len(career_skills)}"
    )

    print(
        "Unique careers:        "
        f"{career_skills['career_key'].nunique()}"
    )

    print(
        "Unique skills:         "
        f"{career_skills['canonical_skill'].nunique()}"
    )

    print(
        f"Skill aliases:         {len(aliases)}"
    )

    print(
        f"Classified edges:      {classified_edges}"
    )

    if classified_edges == len(career_skills):
        print(
            "\nAll graph edges classified correctly."
        )
    else:
        print(
            "\nWARNING: Classified edge count does "
            "not match total graph edges."
        )


if __name__ == "__main__":
    main()