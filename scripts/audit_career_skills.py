import pandas as pd

DATA_PATH = "data/processed/final_career_skills.csv"

df = pd.read_csv(DATA_PATH)

career = df[
    df["career_key"] == "backend_developer"
].copy()

print("\nBACKEND DEVELOPER SKILL AUDIT")
print("-" * 40)
print("Total associations:", len(career))

# Compare clearly relevant and questionable entries.
sample_skills = [
    "Python",
    "Docker",
    "SQL",
    "PostgreSQL",
    "Node.js",
    "Express",
    "Adobe Photoshop",
    "Adobe After Effects",
    "Adobe InDesign",
    "Ada",
]

columns = [
    "canonical_skill",
    "source_onet",
    "source_stackoverflow",
    "onet_direct",
    "onet_related",
    "onet_importance",
    "stackoverflow_count",
    "stackoverflow_frequency",
]

print("\nSELECTED SKILL EVIDENCE")
print("-" * 40)

print(
    career[
        career["canonical_skill"].isin(sample_skills)
    ][columns].to_string(index=False)
)

# Examine the numerical evidence.
career["stackoverflow_frequency"] = pd.to_numeric(
    career["stackoverflow_frequency"],
    errors="coerce",
)

career["onet_importance"] = pd.to_numeric(
    career["onet_importance"],
    errors="coerce",
)

print("\nTOP 20 BY STACK OVERFLOW FREQUENCY")
print("-" * 40)

top = career.sort_values(
    "stackoverflow_frequency",
    ascending=False,
).head(20)

print(
    top[
        [
            "canonical_skill",
            "stackoverflow_frequency",
            "onet_importance",
        ]
    ].to_string(index=False)
)

print("\nEVIDENCE VALUE RANGES")
print("-" * 40)

print(
    career[
        [
            "stackoverflow_frequency",
            "onet_importance",
        ]
    ].describe().to_string()
)