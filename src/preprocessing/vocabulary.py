from collections import defaultdict
from pathlib import Path
import re

import pandas as pd

from src.preprocessing.loader import load_csv, load_csv_from_zip
from src.preprocessing.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR


ONET_ZIP = RAW_DATA_DIR / "onet" / "db_31_0_csv.zip"

ONET_ESSENTIAL_SKILLS = "db_31_0_csv/essential_skills.csv"
ONET_SOFTWARE_SKILLS = "db_31_0_csv/software_skills.csv"

STACKOVERFLOW_FILE = (
    RAW_DATA_DIR / "stackoverflow" / "results.txt"
)


STACKOVERFLOW_SKILL_COLUMNS = {
    "LanguageHaveWorkedWith": "programming_language",
    "DatabaseHaveWorkedWith": "database",
    "PlatformHaveWorkedWith": "platform",
    "WebframeHaveWorkedWith": "web_framework",
    "DevEnvsHaveWorkedWith": "development_environment",
    "SOTagsHaveWorkedWith": "technology_tag",
}


MANUAL_ALIASES = {
    "Amazon Web Services (AWS)": [
        "aws",
        "amazon web services",
    ],
    "Microsoft Azure": [
        "azure",
    ],
    "Google Cloud": [
        "gcp",
        "google cloud platform",
    ],
    "PostgreSQL": [
        "postgres",
        "postgresql",
    ],
    "JavaScript": [
        "javascript",
        "js",
    ],
    "TypeScript": [
        "typescript",
        "ts",
    ],
    "Node.js": [
        "node.js",
        "nodejs",
    ],
    "Visual Studio Code": [
        "visual studio code",
        "vscode",
        "vs code",
    ],
}


def normalize_text(value: str) -> str:
    """Create a normalized comparison key."""
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    return value.casefold()


def clean_display_name(value: str) -> str:
    """Clean whitespace while preserving original technology naming."""
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    return value


def split_multi_value(value: str) -> list[str]:
    """Split Stack Overflow semicolon-delimited skill fields."""
    if pd.isna(value):
        return []

    return [
        clean_display_name(item)
        for item in str(value).split(";")
        if item.strip()
    ]


def extract_onet_skills() -> list[dict]:
    """Extract essential and software skills from O*NET."""
    records = []

    essential = load_csv_from_zip(
        ONET_ZIP,
        ONET_ESSENTIAL_SKILLS
    )

    for skill in essential["Element Name"].dropna().unique():
        records.append(
            {
                "skill": clean_display_name(skill),
                "category": "essential_skill",
                "source": "onet",
            }
        )

    software = load_csv_from_zip(
        ONET_ZIP,
        ONET_SOFTWARE_SKILLS
    )

    for skill in software["Workplace Example"].dropna().unique():
        records.append(
            {
                "skill": clean_display_name(skill),
                "category": "software",
                "source": "onet",
            }
        )

    return records


def extract_stackoverflow_skills() -> list[dict]:
    """Extract technologies reported in Stack Overflow survey responses."""
    dataframe = load_csv(STACKOVERFLOW_FILE)

    records = []

    for column, category in STACKOVERFLOW_SKILL_COLUMNS.items():
        if column not in dataframe.columns:
            continue

        for value in dataframe[column].dropna():
            for skill in split_multi_value(value):
                records.append(
                    {
                        "skill": skill,
                        "category": category,
                        "source": "stackoverflow",
                    }
                )

    return records


def build_skill_vocabulary() -> pd.DataFrame:
    """Build one normalized skill vocabulary from all sources."""
    records = (
        extract_onet_skills()
        + extract_stackoverflow_skills()
    )

    grouped = defaultdict(
        lambda: {
            "names": [],
            "categories": set(),
            "sources": set(),
        }
    )

    for record in records:
        key = normalize_text(record["skill"])

        grouped[key]["names"].append(record["skill"])
        grouped[key]["categories"].add(record["category"])
        grouped[key]["sources"].add(record["source"])

    vocabulary_rows = []

    for normalized_key, data in grouped.items():
        canonical_skill = max(
            set(data["names"]),
            key=data["names"].count
        )

        vocabulary_rows.append(
            {
                "canonical_skill": canonical_skill,
                "normalized_key": normalized_key,
                "categories": ";".join(
                    sorted(data["categories"])
                ),
                "source_onet": int(
                    "onet" in data["sources"]
                ),
                "source_stackoverflow": int(
                    "stackoverflow" in data["sources"]
                ),
            }
        )

    vocabulary = pd.DataFrame(vocabulary_rows)

    vocabulary = vocabulary.sort_values(
        "canonical_skill",
        key=lambda column: column.str.casefold()
    ).reset_index(drop=True)

    return vocabulary


def build_skill_aliases(
    vocabulary: pd.DataFrame
) -> pd.DataFrame:
    """Build aliases for canonical skill names."""
    aliases = []

    for skill in vocabulary["canonical_skill"]:
        aliases.append(
            {
                "alias": normalize_text(skill),
                "canonical_skill": skill,
            }
        )

    for canonical_skill, skill_aliases in MANUAL_ALIASES.items():
        for alias in skill_aliases:
            aliases.append(
                {
                    "alias": normalize_text(alias),
                    "canonical_skill": canonical_skill,
                }
            )

    alias_dataframe = pd.DataFrame(aliases)

    alias_dataframe = alias_dataframe.drop_duplicates(
        subset=["alias", "canonical_skill"]
    )

    return alias_dataframe.sort_values(
        ["canonical_skill", "alias"]
    ).reset_index(drop=True)


def save_skill_vocabulary() -> tuple[Path, Path]:
    """Generate and save vocabulary and alias datasets."""
    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    vocabulary = build_skill_vocabulary()
    aliases = build_skill_aliases(vocabulary)

    vocabulary_path = (
        PROCESSED_DATA_DIR / "skill_vocabulary.csv"
    )

    aliases_path = (
        PROCESSED_DATA_DIR / "skill_aliases.csv"
    )

    vocabulary.to_csv(
        vocabulary_path,
        index=False
    )

    aliases.to_csv(
        aliases_path,
        index=False
    )

    return vocabulary_path, aliases_path


if __name__ == "__main__":
    vocabulary_path, aliases_path = save_skill_vocabulary()

    print(f"Vocabulary saved to: {vocabulary_path}")
    print(f"Aliases saved to: {aliases_path}")