from pathlib import Path
import pandas as pd
from src.preprocessing.paths import PROCESSED_DATA_DIR

SKILL_VOCABULARY_PATH = (PROCESSED_DATA_DIR / "skill_vocabulary.csv")
SKILL_ALIASES_PATH = (PROCESSED_DATA_DIR / "skill_aliases.csv")
CAREER_SKILLS_PATH = (PROCESSED_DATA_DIR / "career_skills.csv")

def load_required_datasets() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    required_paths = [
        SKILL_VOCABULARY_PATH,
        SKILL_ALIASES_PATH,
        CAREER_SKILLS_PATH,
    ]
    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(
                f"Required processed dataset not found: {path}"
            )

    vocabulary = pd.read_csv(SKILL_VOCABULARY_PATH)
    aliases = pd.read_csv(SKILL_ALIASES_PATH)
    career_skills = pd.read_csv(CAREER_SKILLS_PATH)
    return vocabulary, aliases, career_skills


def build_final_skill_vocabulary(
    vocabulary: pd.DataFrame,
    career_skills: pd.DataFrame,
) -> pd.DataFrame:
    career_counts = (
        career_skills
        .groupby("canonical_skill")["career_key"]
        .nunique()
        .rename("career_count")
        .reset_index()
    )

    final_vocabulary = vocabulary.merge(
        career_counts,
        on="canonical_skill",
        how="inner",
    )

    total_careers = (career_skills["career_key"].nunique())
    final_vocabulary["career_coverage"] = (
        final_vocabulary["career_count"]
        / total_careers
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

    return final_vocabulary


def build_final_skill_aliases(
    aliases: pd.DataFrame,
    final_vocabulary: pd.DataFrame,
) -> pd.DataFrame:
    valid_skills = set(
        final_vocabulary["canonical_skill"]
    )
    final_aliases = aliases[
        aliases["canonical_skill"].isin(
            valid_skills
        )
    ].copy()
    final_aliases = (
        final_aliases
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
    return final_aliases

def save_final_skill_datasets() -> tuple[
    Path,
    Path,
]:
    (
        vocabulary,
        aliases,
        career_skills,
    ) = load_required_datasets()

    final_vocabulary = (
        build_final_skill_vocabulary(
            vocabulary,
            career_skills,
        )
    )
    final_aliases = (
        build_final_skill_aliases(
            aliases,
            final_vocabulary,
        )
    )
    final_vocabulary_path = (PROCESSED_DATA_DIR / "final_skill_vocabulary.csv")
    final_aliases_path = (PROCESSED_DATA_DIR / "final_skill_aliases.csv")
    final_vocabulary.to_csv(final_vocabulary_path,index=False,)
    final_aliases.to_csv(final_aliases_path, index=False,)
    return (
        final_vocabulary_path,
        final_aliases_path,
    )
if __name__ == "__main__":
    (
        final_vocabulary_path,
        final_aliases_path,
    ) = save_final_skill_datasets()
    print("Final skill vocabulary saved to: "f"{final_vocabulary_path}")
    print("Final skill aliases saved to: "f"{final_aliases_path}")