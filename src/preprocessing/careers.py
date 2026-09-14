from collections import Counter
from pathlib import Path
import pandas as pd
from src.preprocessing.loader import load_csv, load_csv_from_zip
from src.preprocessing.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR

ONET_ZIP = RAW_DATA_DIR / "onet" / "db_31_0_csv.zip"
ONET_OCCUPATIONS = "db_31_0_csv/occupation_data.csv"
STACKOVERFLOW_FILE = (RAW_DATA_DIR / "stackoverflow" / "results.txt")
CAREERS = [
    {
        "career_key": "software_engineer",
        "career_name": "Software Engineer",
        "career_type": "core",
    },
    {
        "career_key": "software_architect",
        "career_name": "Software / Solutions Architect",
        "career_type": "core",
    },
    {
        "career_key": "frontend_developer",
        "career_name": "Frontend Developer",
        "career_type": "core",
    },
    {
        "career_key": "backend_developer",
        "career_name": "Backend Developer",
        "career_type": "core",
    },
    {
        "career_key": "full_stack_developer",
        "career_name": "Full-Stack Developer",
        "career_type": "core",
    },
    {
        "career_key": "mobile_developer",
        "career_name": "Mobile Developer",
        "career_type": "core",
    },
    {
        "career_key": "embedded_developer",
        "career_name": "Embedded Systems Developer",
        "career_type": "core",
    },
    {
        "career_key": "game_developer",
        "career_name": "Game / Graphics Developer",
        "career_type": "core",
    },
    {
        "career_key": "data_scientist",
        "career_name": "Data Scientist",
        "career_type": "core",
    },
    {
        "career_key": "data_engineer",
        "career_name": "Data Engineer",
        "career_type": "core",
    },
    {
        "career_key": "ai_ml_engineer",
        "career_name": "AI / Machine Learning Engineer",
        "career_type": "core",
    },
    {
        "career_key": "data_business_analyst",
        "career_name": "Data / Business Analyst",
        "career_type": "tech_adjacent",
    },
    {
        "career_key": "cybersecurity_analyst",
        "career_name": "Cybersecurity Analyst",
        "career_type": "core",
    },
    {
        "career_key": "cloud_engineer",
        "career_name": "Cloud Engineer",
        "career_type": "core",
    },
    {
        "career_key": "devops_sre",
        "career_name": "DevOps Engineer / SRE",
        "career_type": "core",
    },
    {
        "career_key": "database_engineer",
        "career_name": "Database Engineer / Administrator",
        "career_type": "core",
    },
    {
        "career_key": "qa_test_engineer",
        "career_name": "QA / Test Engineer",
        "career_type": "core",
    },
    {
        "career_key": "systems_network_admin",
        "career_name": "Systems / Network Administrator",
        "career_type": "core",
    },
    {
        "career_key": "it_support",
        "career_name": "IT Support Engineer",
        "career_type": "core",
    },
    {
        "career_key": "ui_ux_designer",
        "career_name": "UI / UX Designer",
        "career_type": "tech_adjacent",
    },
    {
        "career_key": "product_manager",
        "career_name": "Product Manager",
        "career_type": "tech_adjacent",
    },
    {
        "career_key": "it_project_manager",
        "career_name": "IT Project Manager",
        "career_type": "tech_adjacent",
    },
]
STACKOVERFLOW_CAREER_MAP = {
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
ONET_CAREER_MAP = {
    "15-1211.00": [
        ("data_business_analyst", "direct"),
    ],

    "15-1212.00": [
        ("cybersecurity_analyst", "direct"),
    ],

    "15-1231.00": [
        ("it_support", "direct"),
        ("systems_network_admin", "related"),
    ],

    "15-1232.00": [
        ("it_support", "direct"),
    ],

    "15-1241.00": [
        ("systems_network_admin", "direct"),
        ("cloud_engineer", "related"),
    ],

    "15-1242.00": [
        ("database_engineer", "direct"),
    ],

    "15-1243.00": [
        ("database_engineer", "direct"),
        ("data_engineer", "related"),
    ],

    "15-1243.01": [
        ("data_engineer", "direct"),
    ],

    "15-1244.00": [
        ("systems_network_admin", "direct"),
        ("devops_sre", "related"),
    ],

    "15-1251.00": [
        ("software_engineer", "direct"),
    ],

    "15-1252.00": [
        ("software_engineer", "direct"),
        ("backend_developer", "related"),
    ],

    "15-1253.00": [
        ("qa_test_engineer", "direct"),
    ],

    "15-1254.00": [
        ("full_stack_developer", "direct"),
        ("frontend_developer", "related"),
        ("backend_developer", "related"),
    ],

    "15-1255.00": [
        ("ui_ux_designer", "direct"),
        ("frontend_developer", "related"),
    ],

    "15-1299.08": [
        ("software_architect", "direct"),
        ("cloud_engineer", "related"),
    ],

    "15-1299.09": [
        ("it_project_manager", "direct"),
    ],

    "15-2051.00": [
        ("data_scientist", "direct"),
        ("ai_ml_engineer", "related"),
    ],

    "15-2051.01": [
        ("data_business_analyst", "direct"),
    ],
}
def build_career_catalog() -> pd.DataFrame:
    return pd.DataFrame(CAREERS)
def get_stackoverflow_devtype_counts() -> Counter:
    dataframe = load_csv(
        STACKOVERFLOW_FILE,
        usecols=["DevType"],
        low_memory=False,
    )
    counts = Counter()
    for value in dataframe["DevType"].dropna():
        roles = [
            role.strip()
            for role in str(value).split(";")
            if role.strip()
        ]

        counts.update(roles)

    return counts
def build_stackoverflow_mappings() -> pd.DataFrame:
    counts = get_stackoverflow_devtype_counts()
    rows = []
    for source_label, career_key in STACKOVERFLOW_CAREER_MAP.items():
        rows.append(
            {
                "source": "stackoverflow",
                "source_key": source_label,
                "source_label": source_label,
                "career_key": career_key,
                "relationship": "direct",
                "source_count": counts.get(source_label, 0),
            }
        )

    return pd.DataFrame(rows)
def build_onet_mappings() -> pd.DataFrame:
    occupations = load_csv_from_zip(
        ONET_ZIP,
        ONET_OCCUPATIONS,
    )
    occupation_lookup = dict(
        zip(
            occupations["O*NET-SOC Code"],
            occupations["Title"],
        )
    )
    rows = []
    for soc_code, career_links in ONET_CAREER_MAP.items():
        source_label = occupation_lookup.get(
            soc_code,
            "Unknown occupation",
        )
        for career_key, relationship in career_links:
            rows.append(
                {
                    "source": "onet",
                    "source_key": soc_code,
                    "source_label": source_label,
                    "career_key": career_key,
                    "relationship": relationship,
                    "source_count": 1,
                }
            )

    return pd.DataFrame(rows)
def build_source_mappings() -> pd.DataFrame:
    return pd.concat(
        [
            build_stackoverflow_mappings(),
            build_onet_mappings(),
        ],
        ignore_index=True,
    )
def save_career_datasets() -> tuple[Path, Path]:
    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    careers = build_career_catalog()
    mappings = build_source_mappings()
    careers_path = (
        PROCESSED_DATA_DIR / "careers.csv"
    )
    mappings_path = (
        PROCESSED_DATA_DIR / "career_source_mappings.csv"
    )
    careers.to_csv(
        careers_path,
        index=False,
    )
    mappings.to_csv(
        mappings_path,
        index=False,
    )
    return careers_path, mappings_path
if __name__ == "__main__":
    careers_path, mappings_path = save_career_datasets()

    print(f"Careers saved to: {careers_path}")
    print(f"Mappings saved to: {mappings_path}")