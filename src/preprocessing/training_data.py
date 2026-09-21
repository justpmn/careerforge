import re
from pathlib import Path
import numpy as np
import pandas as pd
from src.preprocessing.paths import (RAW_DATA_DIR,PROCESSED_DATA_DIR,)

STACKOVERFLOW_PATH = (RAW_DATA_DIR / "stackoverflow" / "results.txt")
FINAL_VOCABULARY_PATH = (PROCESSED_DATA_DIR/ "final_skill_vocabulary.csv")
FINAL_ALIASES_PATH = (PROCESSED_DATA_DIR/ "final_skill_aliases.csv")

MODEL_VOCABULARY_PATH = (PROCESSED_DATA_DIR / "skill_vocabulary.csv")
MODEL_ALIASES_PATH = (PROCESSED_DATA_DIR / "skill_aliases.csv")

TECH_COLUMNS = [
    "LanguageHaveWorkedWith",
    "DatabaseHaveWorkedWith",
    "PlatformHaveWorkedWith",
    "WebframeHaveWorkedWith",
    "DevEnvsHaveWorkedWith",
    "SOTagsHaveWorkedWith",
]

DEVTYPE_TO_CAREER = {
    "Developer, desktop or enterprise applications":
        "software_engineer",

    "Architect, software or solutions":
        "software_architect",

    "Developer, front-end":
        "frontend_developer",

    "Developer, back-end":
        "backend_developer",

    "Developer, full-stack":
        "full_stack_developer",

    "Developer, mobile":
        "mobile_developer",

    "Developer, embedded applications or devices":
        "embedded_developer",

    "Developer, game or graphics":
        "game_developer",

    "Data scientist":
        "data_scientist",

    "Data engineer":
        "data_engineer",

    "AI/ML engineer":
        "ai_ml_engineer",

    "Developer, AI apps or physical AI":
        "ai_ml_engineer",

    "Data or business analyst":
        "data_business_analyst",

    "Cybersecurity or InfoSec professional":
        "cybersecurity_analyst",

    "Cloud infrastructure engineer":
        "cloud_engineer",

    "DevOps engineer or professional":
        "devops_sre",

    "Database administrator or engineer":
        "database_engineer",

    "Developer, QA or test":
        "qa_test_engineer",

    "System administrator":
        "systems_network_admin",

    "Support engineer or analyst":
        "it_support",

    "UX, Research Ops or UI design professional":
        "ui_ux_designer",

    "Product manager":
        "product_manager",

    "Project manager":
        "it_project_manager",
}

EXPECTED_CAREERS = {
    "software_engineer",
    "software_architect",
    "frontend_developer",
    "backend_developer",
    "full_stack_developer",
    "mobile_developer",
    "embedded_developer",
    "game_developer",
    "data_scientist",
    "data_engineer",
    "ai_ml_engineer",
    "data_business_analyst",
    "cybersecurity_analyst",
    "cloud_engineer",
    "devops_sre",
    "database_engineer",
    "qa_test_engineer",
    "systems_network_admin",
    "it_support",
    "ui_ux_designer",
    "product_manager",
    "it_project_manager",
}

def normalize_skill_key(value: str) -> str:
    #  Normalize a Stack Overflow tech value for alias lookup.
    
    value = str(value).strip().casefold()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value
"""
def load_skill_resources() -> tuple[
    list[str],
    dict[str, str],
]:
    # load final vocal
    vocabulary = pd.read_csv(FINAL_VOCABULARY_PATH)
    aliases = pd.read_csv(FINAL_ALIASES_PATH)
    feature_names = (
        vocabulary["canonical_skill"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    alias_lookup = {
        normalize_skill_key(alias):
            canonical_skill

        for alias, canonical_skill
        in zip(
            aliases["alias"],
            aliases["canonical_skill"],
        )
    }

    # Always allow canonical skill names
    # to match themselves.
    for skill in feature_names:
        alias_lookup.setdefault(
            normalize_skill_key(skill),
            skill,
        )

    return (feature_names, alias_lookup)

"""
"""
def load_skill_resources() -> tuple[
    list[str],
    dict[str, str],
]:
    # Load candidate model vocabulary
    vocabulary = pd.read_csv(MODEL_VOCABULARY_PATH)
    aliases = pd.read_csv(MODEL_ALIASES_PATH)

    feature_names = (
        vocabulary["canonical_skill"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    feature_set = set(feature_names)

    # Keep only aliases belonging to model features
    aliases = aliases[
        aliases["canonical_skill"].isin(feature_set)
    ].copy()

    alias_lookup = {
        normalize_skill_key(alias): canonical_skill
        for alias, canonical_skill in zip(
            aliases["alias"],
            aliases["canonical_skill"],
        )
    }

    # Always allow canonical skill names
    # to match themselves.
    for skill in feature_names:
        alias_lookup.setdefault(
            normalize_skill_key(skill),
            skill,
        )

    return feature_names, alias_lookup
"""
def load_skill_resources() -> tuple[
    list[str],
    dict[str, str],
]:
    # Load candidate model vocabulary
    vocabulary = pd.read_csv(MODEL_VOCABULARY_PATH)
    aliases = pd.read_csv(MODEL_ALIASES_PATH)

    feature_names = (
        vocabulary["canonical_skill"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    feature_set = set(feature_names)

    # Keep only aliases belonging to model features
    aliases = aliases[
        aliases["canonical_skill"].isin(feature_set)
    ].copy()

    alias_lookup = {
        normalize_skill_key(alias): canonical_skill
        for alias, canonical_skill in zip(
            aliases["alias"],
            aliases["canonical_skill"],
        )
    }

    # Always allow canonical skill names
    # to match themselves.
    for skill in feature_names:
        alias_lookup.setdefault(
            normalize_skill_key(skill),
            skill,
        )

    return feature_names, alias_lookup
def split_technology_values(
    value,
) -> list[str]:
    """
    Split semicolon-separated stackoverflow tech answers.
    """
    if pd.isna(value):
        return []

    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip()
    ]


def extract_respondent_skills(
    row: pd.Series,
    alias_lookup: dict[str, str],
    valid_skills: set[str],
) -> set[str]:
    """
    Convert a respondent's stackoverflow technologies into canonical skills.
    """
    detected = set()
    for column in TECH_COLUMNS:

        for raw_skill in split_technology_values(
            row[column]
        ):
            normalized = normalize_skill_key(
                raw_skill
            )

            canonical_skill = (
                alias_lookup.get(normalized)
            )

            if (
                canonical_skill
                and canonical_skill in valid_skills
            ):
                detected.add(canonical_skill)

    return detected

def build_rf_training_dataset() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Build respondent-level binary skill vectors with one CareerForge career target per row.
    """
    (
        feature_names,
        alias_lookup,
    ) = load_skill_resources()

    required_columns = [
        "ResponseId",
        "DevType",
        *TECH_COLUMNS,
    ]
    survey = pd.read_csv(
        STACKOVERFLOW_PATH,
        usecols=required_columns,
        low_memory=False,
    )
    print(
        f"Raw Stack Overflow respondents: "
        f"{len(survey):,}"
    )

    survey["career_key"] = (
        survey["DevType"]
        .map(DEVTYPE_TO_CAREER)
    )

    mapped = (
        survey[
            survey["career_key"].notna()
        ]
        .copy()
        .reset_index(drop=True)
    )

    print(
        f"Mapped CareerForge respondents: "
        f"{len(mapped):,}"
    )
    valid_skills = set(feature_names)

    vectors = []
    response_ids = []
    careers = []

    feature_index = {
        skill: index
        for index, skill
        in enumerate(feature_names)
    }

    for _, row in mapped.iterrows():

        respondent_skills = (
            extract_respondent_skills(
                row,
                alias_lookup,
                valid_skills,
            )
        )

        # No usable skill evidence means this row cannot train our skill-based model. 
        if not respondent_skills:
            continue
        vector = np.zeros(
            len(feature_names),
            dtype=np.uint8,
        )

        for skill in respondent_skills:
            vector[
                feature_index[skill]
            ] = 1

        vectors.append(vector)

        response_ids.append(
            row["ResponseId"]
        )

        careers.append(
            row["career_key"]
        )

    if not vectors:
        raise ValueError(
            "No usable training rows were generated."
        )

    feature_matrix = pd.DataFrame(
        np.vstack(vectors),
        columns=feature_names,
        dtype=np.uint8,
    )

    # Remove skills that never occur in Stack Overflow.
    # Some final CareerForge skills come only from O*NET.
    # They remain useful for the knowledge graph and
    # skill-gap analysis, but they cannot teach the RF
    # anything if every training row contains 0.
    observed_mask = (feature_matrix.sum(axis=0) > 0)

    feature_matrix = (
        feature_matrix.loc[
            :,
            observed_mask,
        ]
        .copy()
    )

    metadata = pd.DataFrame(
        {
            "response_id": response_ids,
            "career_key": careers,
        }
    )

    training_data = pd.concat(
        [
            metadata.reset_index(drop=True),
            feature_matrix.reset_index(
                drop=True
            ),
        ],
        axis=1,
    )

    class_distribution = (
        training_data[
            "career_key"
        ]
        .value_counts()
        .rename_axis(
            "career_key"
        )
        .reset_index(
            name="samples"
        )
    )

    feature_metadata = pd.DataFrame(
        {
            "feature_index":
                range(
                    feature_matrix.shape[1]
                ),

            "canonical_skill":
                feature_matrix.columns,
        }
    )

    return (
        training_data,
        feature_metadata,
        class_distribution,
    )


def save_rf_training_dataset() -> tuple[
    Path,
    Path,
    Path,
]:
    """
    Generate and save the Random Forest training artifacts.
    """
    (
        training_data,
        feature_metadata,
        class_distribution,
    ) = build_rf_training_dataset()

    training_path = (PROCESSED_DATA_DIR / "rf_training_data.parquet")
    features_path = (PROCESSED_DATA_DIR / "rf_feature_names.csv")
    distribution_path = (PROCESSED_DATA_DIR / "rf_class_distribution.csv")
    training_data.to_parquet(training_path,index=False)
    feature_metadata.to_csv(features_path,index=False)
    class_distribution.to_csv( distribution_path, index=False)
    return (training_path, features_path, distribution_path)