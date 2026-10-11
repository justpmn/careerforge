import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

csv_path = ROOT / "data/processed/rf_feature_names.csv"
metadata_path = ROOT / "models/careerforge_rf_v1_metadata.json"

with open(csv_path, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

csv_features = [
    row["canonical_skill"]
    for row in rows
]

with open(metadata_path, encoding="utf-8") as f:
    metadata = json.load(f)

print("\nRF FEATURE ALIGNMENT AUDIT")
print("-" * 45)

print("CSV feature count:", len(csv_features))
print("Metadata feature count:", metadata.get("feature_count"))
print("Metadata keys:", list(metadata.keys()))

model_features = None

for key in [
    "feature_names",
    "feature_columns",
    "features",
    "skill_features",
]:
    value = metadata.get(key)

    if isinstance(value, list) and all(
        isinstance(item, str) for item in value
    ):
        model_features = value
        print("Feature list key:", key)
        break

if model_features is not None:
    model_feature_set = set(model_features)

    filtered_csv_features = [
        skill
        for skill in csv_features
        if skill in model_feature_set
    ]

    print("\nFINAL ALIGNMENT CHECK")
    print("-" * 45)

    print(
        "Selected CSV feature count:",
        len(filtered_csv_features),
    )

    print(
        "Selected features preserve model order:",
        filtered_csv_features == model_features,
    )

    print(
        "Extra CSV features:",
        len(set(csv_features) - model_feature_set),
    )

    print(
        "Duplicate CSV feature names:",
        len(csv_features) - len(set(csv_features)),
    )

    print("Model metadata features:", len(model_features))
    print("Exact feature order matches:",
          csv_features == model_features)

    print("\nIN CSV BUT NOT IN MODEL METADATA")
    print(sorted(set(csv_features) - set(model_features)))

    print("\nIN MODEL METADATA BUT NOT CSV")
    print(sorted(set(model_features) - set(csv_features)))

    print("\nSELECTED SKILLS")
    for skill in [
        "Docker",
        "FastAPI",
        "Git",
        "GitHub",
        "RESTful API",
        "Cloudflare",
        "Adobe Photoshop",
    ]:
        print(
            f"{skill:20}",
            f"CSV={skill in csv_features}",
            f"Model={skill in model_features}",
        )

else:
    print(
        "Could not identify metadata feature list. "
        "Inspect the metadata keys above."
    )