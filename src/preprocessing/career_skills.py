from collections import Counter, defaultdict
from pathlib import Path
import pandas as pd
from src.preprocessing.careers import (ONET_CAREER_MAP,STACKOVERFLOW_CAREER_MAP)
from src.preprocessing.loader import load_csv, load_csv_from_zip
from src.preprocessing.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.preprocessing.vocabulary import (
    ONET_ESSENTIAL_SKILLS,
    ONET_SOFTWARE_SKILLS,
    ONET_ZIP,
    STACKOVERFLOW_FILE,
    STACKOVERFLOW_SKILL_COLUMNS,
    clean_display_name,
    normalize_text,
    split_multi_value,
)
DIRECT_RELATIONSHIP = "direct"
RELATED_RELATIONSHIP = "related"
def get_canonical_skill_lookup() -> dict[str, str]:
    catalog_path = PROCESSED_DATA_DIR / "skill_catalog.csv"
    if not catalog_path.exists():
        raise FileNotFoundError(
            "skill_catalog.csv does not exist. "
            "Run `python -m src.preprocessing.vocabulary` first."
        )
    catalog = pd.read_csv(catalog_path)
    return dict(
        zip(
            catalog["normalized_key"],
            catalog["canonical_skill"],
        )
    )

"""
def get_skill_alias_lookup() -> dict[str, str]:
    aliases_path = PROCESSED_DATA_DIR / "skill_aliases.csv"
    if not aliases_path.exists():
        raise FileNotFoundError(
            "skill_aliases.csv does not exist. "
            "Run `python -m src.preprocessing.vocabulary` first to generate the file."
        )
        aliases = pd.read_csv(aliases_path)
        
        return dict(
            zip(
                aliases["alias"],
                aliases["canonical_skill"],
            )
        )
        
"""
def get_skill_alias_lookup() -> dict[str, str]:
    aliases_path = PROCESSED_DATA_DIR / "skill_aliases.csv"
    if not aliases_path.exists():
        raise FileNotFoundError(
            "skill_aliases.csv does not exist. "
            "Run vocabulary first to generate the file."
        )
    aliases = pd.read_csv(aliases_path)
    alias_lookup = dict(
        zip(
            aliases["alias"],
            aliases["canonical_skill"],
        )
    )
    
    return alias_lookup

def canonicalize_skill(
    skill: str,
    catalog_lookup: dict[str, str],
    alias_lookup: dict[str, str],
) -> str:
    cleaned = clean_display_name(skill)
    normalized = normalize_text(cleaned)
    
    if normalized in catalog_lookup:
        return catalog_lookup[normalized]
    
    if normalized in alias_lookup:
        return alias_lookup[normalized]

    return cleaned


def build_onet_career_skills() -> pd.DataFrame:
    canonical_lookup = get_canonical_skill_lookup()
    alias_lookup = get_skill_alias_lookup()

    rows = []

    essential = load_csv_from_zip(
        ONET_ZIP,
        ONET_ESSENTIAL_SKILLS,
    )
    essential = essential[
        essential["Scale ID"] == "IM"
    ].copy()

    for _, row in essential.iterrows():
        soc_code = row["O*NET-SOC Code"]

        if soc_code not in ONET_CAREER_MAP:
            continue

        skill = canonicalize_skill(
            row["Element Name"],
            canonical_lookup,
            alias_lookup,
        )

        for career_key, relationship in ONET_CAREER_MAP[soc_code]:
            rows.append(
                {
                    "career_key": career_key,
                    "canonical_skill": skill,
                    "skill_type": "essential_skill",
                    "source": "onet",
                    "source_key": soc_code,
                    "relationship": relationship,
                    "evidence_count": 1,
                    "importance": row["Data Value"],
                    "hot_technology": 0,
                    "in_demand": 0,
                }
            )

    software = load_csv_from_zip(
        ONET_ZIP,
        ONET_SOFTWARE_SKILLS,
    )

    for _, row in software.iterrows():
        soc_code = row["O*NET-SOC Code"]

        if soc_code not in ONET_CAREER_MAP:
            continue

        raw_skill = row["Workplace Example"]

        if pd.isna(raw_skill):
            continue

        skill = canonicalize_skill(
            raw_skill,
            canonical_lookup,
            alias_lookup,
        )

        for career_key, relationship in ONET_CAREER_MAP[soc_code]:
            rows.append(
                {
                    "career_key": career_key,
                    "canonical_skill": skill,
                    "skill_type": "software",
                    "source": "onet",
                    "source_key": soc_code,
                    "relationship": relationship,
                    "evidence_count": 1,
                    "importance": pd.NA,
                    "hot_technology": int(
                        str(
                            row.get(
                                "Hot Technology",
                                "",
                            )
                        ).strip().upper()
                        == "Y"
                    ),
                    "in_demand": int(
                        str(
                            row.get(
                                "In Demand",
                                "",
                            )
                        ).strip().upper()
                        == "Y"
                    ),
                }
            )

    return pd.DataFrame(rows)


def build_stackoverflow_career_skills() -> pd.DataFrame:
    canonical_lookup = get_canonical_skill_lookup()
    alias_lookup = get_skill_alias_lookup()

    columns = [
        "DevType",
        *STACKOVERFLOW_SKILL_COLUMNS.keys(),
    ]

    dataframe = load_csv(
        STACKOVERFLOW_FILE,
        usecols=lambda column: column in columns,
        low_memory=False,
    )

    pair_counts = Counter()
    career_observations = Counter()
    skill_categories = defaultdict(set)

    for _, row in dataframe.iterrows():
        devtype_value = row.get("DevType")

        if pd.isna(devtype_value):
            continue

        source_roles = [
            value.strip()
            for value in str(devtype_value).split(";")
            if value.strip()
        ]
        career_keys = {
            STACKOVERFLOW_CAREER_MAP[source_role]
            for source_role in source_roles
            if source_role in STACKOVERFLOW_CAREER_MAP
        }

        if not career_keys:
            continue

        skills = {}

        for column, category in STACKOVERFLOW_SKILL_COLUMNS.items():
            value = row.get(column)

            for raw_skill in split_multi_value(value):
                canonical_skill = canonicalize_skill(
                    raw_skill,
                    canonical_lookup,
                    alias_lookup,
                )

                skills[canonical_skill] = True
                skill_categories[canonical_skill].add(category)

        for career_key in career_keys:
            career_observations[career_key] += 1

            for canonical_skill in skills:
                pair_counts[
                    (career_key, canonical_skill)
                ] += 1

    rows = []

    for (career_key, skill), count in pair_counts.items():
        total = career_observations[career_key]

        frequency = (
            count / total
            if total
            else 0.0
        )

        rows.append(
            {
                "career_key": career_key,
                "canonical_skill": skill,
                "skill_type": ";".join(
                    sorted(skill_categories[skill])
                ),
                "source": "stackoverflow",
                "source_key": "DevType",
                "relationship": DIRECT_RELATIONSHIP,
                "evidence_count": count,
                "career_observations": total,
                "frequency": frequency,
            }
        )

    return pd.DataFrame(rows)


def build_combined_career_skills(
    onet: pd.DataFrame,
    stackoverflow: pd.DataFrame,
) -> pd.DataFrame:
    evidence = defaultdict(
        lambda: {
            "source_onet": 0,
            "source_stackoverflow": 0,
            "onet_direct": 0,
            "onet_related": 0,
            "onet_importance": [],
            "stackoverflow_count": 0,
            "stackoverflow_frequency": 0.0,
            "hot_technology": 0,
            "in_demand": 0,
            "skill_types": set(),
        }
    )
    for _, row in onet.iterrows():
        key = (
            row["career_key"],
            row["canonical_skill"],
        )

        item = evidence[key]

        item["source_onet"] = 1
        item["skill_types"].add(
            row["skill_type"]
        )

        if row["relationship"] == DIRECT_RELATIONSHIP:
            item["onet_direct"] = 1
        elif row["relationship"] == RELATED_RELATIONSHIP:
            item["onet_related"] = 1

        if pd.notna(row["importance"]):
            item["onet_importance"].append(
                float(row["importance"])
            )

        item["hot_technology"] = max(
            item["hot_technology"],
            int(row["hot_technology"]),
        )

        item["in_demand"] = max(
            item["in_demand"],
            int(row["in_demand"]),
        )

    for _, row in stackoverflow.iterrows():
        key = (
            row["career_key"],
            row["canonical_skill"],
        )

        item = evidence[key]

        item["source_stackoverflow"] = 1

        for skill_type in str(row["skill_type"]).split(";"):
            if skill_type:
                item["skill_types"].add(
                    skill_type
                )

        item["stackoverflow_count"] = int(
            row["evidence_count"]
        )

        item["stackoverflow_frequency"] = float(
            row["frequency"]
        )

    rows = []
    for (career_key, skill), item in evidence.items():
        importance_values = item["onet_importance"]

        mean_importance = (
            sum(importance_values)
            / len(importance_values)
            if importance_values
            else pd.NA
        )
        rows.append(
            {
                "career_key": career_key,
                "canonical_skill": skill,
                "skill_types": ";".join(
                    sorted(item["skill_types"])
                ),
                "source_onet": item["source_onet"],
                "source_stackoverflow":
                    item["source_stackoverflow"],
                "onet_direct": item["onet_direct"],
                "onet_related": item["onet_related"],
                "onet_importance": mean_importance,
                "stackoverflow_count":
                    item["stackoverflow_count"],
                "stackoverflow_frequency":
                    item["stackoverflow_frequency"],
                "hot_technology":
                    item["hot_technology"],
                "in_demand":
                    item["in_demand"],
            }
        )
    combined = pd.DataFrame(rows)
    return combined.sort_values(
        [
            "career_key",
            "source_stackoverflow",
            "stackoverflow_frequency",
        ],
        ascending=[
            True,
            False,
            False,
        ],
    ).reset_index(drop=True)


def save_career_skill_datasets() -> tuple[Path, Path, Path]:
    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    onet = build_onet_career_skills()
    stackoverflow = build_stackoverflow_career_skills()
    combined = build_combined_career_skills(
        onet,
        stackoverflow,
    )
    onet_path = (
        PROCESSED_DATA_DIR
        / "onet_career_skills.csv"
    )
    stackoverflow_path = (
        PROCESSED_DATA_DIR
        / "stackoverflow_career_skills.csv"
    )
    combined_path = (
        PROCESSED_DATA_DIR
        / "career_skills.csv"
    )
    onet.to_csv(
        onet_path,
        index=False,
    )
    stackoverflow.to_csv(
        stackoverflow_path,
        index=False,
    )
    combined.to_csv(
        combined_path,
        index=False,
    )
    return (
        onet_path,
        stackoverflow_path,
        combined_path,
    )
if __name__ == "__main__":
    (
        onet_path,
        stackoverflow_path,
        combined_path,
    ) = save_career_skill_datasets()

    print(f"O*NET career skills saved to: {onet_path}")
    print(
        "Stack Overflow career skills saved to: "
        f"{stackoverflow_path}"
    )
    print(f"Combined career skills saved to: {combined_path}")