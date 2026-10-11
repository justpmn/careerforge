import csv
from pathlib import Path

from src.backend.app.services.competency_profile_loader import (
    load_all_profiles,
)


ROOT = Path(__file__).resolve().parents[1]

VOCAB_PATH = (
    ROOT / "data/processed/final_skill_vocabulary.csv"
)

EXPECTED_CAREERS = {
    "backend_developer",
    "frontend_developer",
    "data_engineer",
}


def main():
    profiles = load_all_profiles()

    with VOCAB_PATH.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        catalog = {
            row["canonical_skill"]
            for row in csv.DictReader(file)
        }

    errors = []

    print("\nCOMPETENCY PROFILE VALIDATION")
    print("-" * 45)

    for career_key, groups in profiles.items():
        print(
            f"{career_key}: {len(groups)} groups"
        )

        for group in groups:
            for skill in group["any_of"]:
                if skill not in catalog:
                    errors.append(
                        f"{career_key}/{group['key']}: "
                        f"Unknown skill '{skill}'"
                    )

    missing_careers = EXPECTED_CAREERS - set(profiles)

    if missing_careers:
        errors.append(
            f"Missing profiles: {sorted(missing_careers)}"
        )

    print("\nCAREERS LOADED:", len(profiles))

    if errors:
        for error in errors:
            print("ERROR:", error)

        raise SystemExit(1)

    print("All profiles validated successfully.")


if __name__ == "__main__":
    main()