
import json
from pathlib import Path

from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)
from src.backend.app.services.competency_templates import (
    COMMON_COMPETENCIES,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "src"
    / "backend"
    / "app"
    / "competency_profiles"
)


def export_profiles():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for career_key, competencies in (
        CAREER_COMPETENCY_PROFILES.items()
    ):
        groups = []
        shared_count = 0

        for group in competencies:
            key = group["key"]

            # Replace exact shared definitions
            # with references to our templates.
            if group == COMMON_COMPETENCIES.get(key):
                groups.append({
                    "template": key
                })
                shared_count += 1
            else:
                groups.append(group)

        profile = {
            "career_key": career_key,
            "version": 1,
            "groups": groups,
        }

        output_path = OUTPUT_DIR / f"{career_key}.json"

        if output_path.exists():
            raise FileExistsError(
                f"Profile already exists: {output_path}"
            )

        output_path.write_text(
            json.dumps(profile, indent=2) + "\n",
            encoding="utf-8",
        )

        print(
            f"{career_key}: "
            f"{len(groups)} competency groups, "
            f"{shared_count} shared templates"
        )

    print("\nProfile export complete.")


if __name__ == "__main__":
    export_profiles()
