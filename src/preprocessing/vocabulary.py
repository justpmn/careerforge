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
        "amazon aws",
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
        "node",
    ],
    "Visual Studio Code": [
        "visual studio code",
        "vscode",
        "vs code",
    ],
}


def normalize_text(value: str) -> str:
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    return value.casefold()


def clean_display_name(value: str) -> str:
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)

    return value


def split_multi_value(value: str) -> list[str]:
    if pd.isna(value):
        return []

    return [
        clean_display_name(item)
        for item in str(value).split(";")
        if item.strip()
    ]


def extract_onet_skills() -> list[dict]:
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
                "hot_technology": False,
                "in_demand": False,
            }
        )

    software = load_csv_from_zip(
        ONET_ZIP,
        ONET_SOFTWARE_SKILLS
    )

    for _, row in software.iterrows():
        skill = row.get("Workplace Example")

        if pd.isna(skill):
            continue

        records.append(
            {
                "skill": clean_display_name(skill),
                "category": "software",
                "source": "onet",
                "hot_technology": (
                    str(row.get("Hot Technology", "")).strip().upper()
                    == "Y"
                ),
                "in_demand": (
                    str(row.get("In Demand", "")).strip().upper()
                    == "Y"
                ),
            }
        )

    return records


def extract_stackoverflow_skills() -> list[dict]:
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
                        "hot_technology": False,
                        "in_demand": False,
                    }
                )

    return records


def build_skill_catalog() -> pd.DataFrame:
    records = (
        extract_onet_skills()
        + extract_stackoverflow_skills()
    )

    grouped = defaultdict(
        lambda: {
            "names": [],
            "categories": set(),
            "sources": set(),
            "hot_technology": False,
            "in_demand": False,
        }
    )
    for record in records:
        key = normalize_text(record["skill"])

        if not key:
            continue

        grouped[key]["names"].append(record["skill"])
        grouped[key]["categories"].add(record["category"])
        grouped[key]["sources"].add(record["source"])

        grouped[key]["hot_technology"] = (
            grouped[key]["hot_technology"]
            or record["hot_technology"]
        )

        grouped[key]["in_demand"] = (
            grouped[key]["in_demand"]
            or record["in_demand"]
        )

    rows = []

    for normalized_key, data in grouped.items():
        canonical_skill = max(
            set(data["names"]),
            key=data["names"].count
        )

        rows.append(
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
                "hot_technology": int(
                    data["hot_technology"]
                ),
                "in_demand": int(
                    data["in_demand"]
                ),
            }
        )
    catalog = pd.DataFrame(rows)

    return catalog.sort_values(
        "canonical_skill",
        key=lambda column: column.str.casefold()
    ).reset_index(drop=True)


def build_skill_vocabulary(
    catalog: pd.DataFrame
) -> pd.DataFrame:
    mask = (
        (catalog["source_stackoverflow"] == 1)
        | (catalog["hot_technology"] == 1)
        | (catalog["in_demand"] == 1)
    )

    vocabulary = catalog.loc[mask].copy()

    return vocabulary.reset_index(drop=True)
def build_skill_aliases(
    vocabulary: pd.DataFrame
) -> pd.DataFrame:
    aliases = []
    canonical_skills = set(
        vocabulary["canonical_skill"]
    )
    for skill in canonical_skills:
        aliases.append(
            {
                "alias": normalize_text(skill),
                "canonical_skill": skill,
            }
        )
    for canonical_skill, skill_aliases in MANUAL_ALIASES.items():
        if canonical_skill not in canonical_skills:
            continue
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
def save_skill_datasets() -> tuple[Path, Path, Path]:
    """Generate the catalog, matcher vocabulary, and aliases."""
    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )
    catalog = build_skill_catalog()
    vocabulary = build_skill_vocabulary(catalog)
    aliases = build_skill_aliases(vocabulary)
    catalog_path = (
        PROCESSED_DATA_DIR / "skill_catalog.csv"
    )
    vocabulary_path = (
        PROCESSED_DATA_DIR / "skill_vocabulary.csv"
    )
    aliases_path = (
        PROCESSED_DATA_DIR / "skill_aliases.csv"
    )
    catalog.to_csv(
        catalog_path,
        index=False
    )
    vocabulary.to_csv(
        vocabulary_path,
        index=False
    )
    aliases.to_csv(
        aliases_path,
        index=False
    )
    return catalog_path, vocabulary_path, aliases_path
if __name__ == "__main__":
    catalog_path, vocabulary_path, aliases_path = (
        save_skill_datasets()
    )
    print(f"Skill catalog saved to: {catalog_path}")
    print(f"Skill vocabulary saved to: {vocabulary_path}")
    print(f"Skill aliases saved to: {aliases_path}")