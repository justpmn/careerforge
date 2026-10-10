import pandas as pd

PATH = "data/processed/final_career_skills.csv"

df = pd.read_csv(PATH)

numeric_columns = [
    "source_onet",
    "source_stackoverflow",
    "onet_direct",
    "onet_importance",
    "stackoverflow_frequency",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )

results = []

for career_key, group in df.groupby("career_key"):

    frequency = group[
        "stackoverflow_frequency"
    ].fillna(0)

    onet_only = (
        (group["source_onet"] == 1)
        & (group["source_stackoverflow"] == 0)
    )

    results.append({
        "career": career_key,
        "total": len(group),
        "so_supported": int(
            (frequency > 0).sum()
        ),
        "freq_2pct": int(
            (frequency >= 0.02).sum()
        ),
        "freq_5pct": int(
            (frequency >= 0.05).sum()
        ),
        "onet_only": int(onet_only.sum()),
        "onet_direct": int(
            (group["onet_direct"] == 1).sum()
        ),
        "importance_available": int(
            group["onet_importance"].notna().sum()
        ),
    })

summary = pd.DataFrame(results)

print("\nCAREER EVIDENCE COVERAGE")
print("-" * 80)
print(summary.to_string(index=False))

print("\nCAREERS WITH LOW 5% COVERAGE")
print("-" * 80)

low_coverage = summary[
    summary["freq_5pct"] < 10
]

print(
    low_coverage.to_string(index=False)
    if not low_coverage.empty
    else "None"
)

print("\nBACKEND DEVELOPER: TOP 25 BY FREQUENCY")
print("-" * 80)

backend = df[
    df["career_key"] == "backend_developer"
].sort_values(
    "stackoverflow_frequency",
    ascending=False,
).head(25)

print(
    backend[
        [
            "canonical_skill",
            "stackoverflow_frequency",
            "source_onet",
            "source_stackoverflow",
        ]
    ].to_string(index=False)
)