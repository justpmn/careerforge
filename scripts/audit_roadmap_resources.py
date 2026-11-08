"""Read-only learning-resource coverage audit for CareerForge.

Run from the repository root:
    python -m scripts.audit_roadmap_resources
    python -m scripts.audit_roadmap_resources --career backend_developer

This script never creates, edits, or deletes database records.
"""

import argparse
from urllib.parse import urlparse

from src.backend.app.database.session import get_db
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)
from src.backend.app.services.learning_resource_service import (
    get_resources_for_competencies,
    get_resources_for_skills,
)


def valid_url(raw_url: object) -> bool:
    if not isinstance(raw_url, str):
        return False
    url = urlparse(raw_url)
    return url.scheme in ("http", "https") and bool(url.netloc)


def describe(resources: list[dict]) -> None:
    for resource in resources[:4]:
        title = resource.get("title", "Untitled resource")
        provider = resource.get("provider") or "Unknown provider"
        url = resource.get("url")
        warning = " [MISSING/INVALID URL]" if not valid_url(url) else ""
        print(f"      - {title} ({provider}){warning}")
        if url:
            print(f"        {url}")
    if len(resources) > 4:
        print(f"      ... plus {len(resources) - 4} more")


def audit_career(db, career_key: str) -> int:
    profile = CAREER_COMPETENCY_PROFILES.get(career_key)
    if not profile:
        raise ValueError(f"No competency profile: {career_key}")

    keys = [item["key"] for item in profile]
    by_competency = get_resources_for_competencies(db, keys, career_key)

    print(f"\nCAREER: {career_key} ({len(keys)} competencies)")
    print("=" * 72)
    missing = []
    for item in profile:
        key = item["key"]
        resources = by_competency.get(key, [])
        print(f"  {key:<28} {len(resources):>2} database resource(s)")
        if not resources:
            missing.append(key)
        else:
            describe(resources)

    if career_key == "data_scientist":
        # Python is a template-only foundation node, not one of the ten
        # career competency profile keys. Check canonical skill links too.
        python_resources = get_resources_for_skills(db, ["Python"])
        print(f"\n  {'python (foundation)':<28} {len(python_resources):>2} skill resource(s)")
        describe(python_resources)
        if not python_resources:
            missing.append("python (foundation)")

    covered = len(keys) - sum(key in missing for key in keys)
    print(f"\nCOMPETENCY COVERAGE: {covered}/{len(keys)}")
    if missing:
        print("MISSING DATABASE LINKS:")
        for key in missing:
            print(f"  - {key}")
    else:
        print("All assessed competencies have database resource links.")
    return len(missing)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--career", default="data_scientist")
    args = parser.parse_args()

    db_generator = get_db()
    try:
        db = next(db_generator)
        audit_career(db, args.career)
    finally:
        db_generator.close()


if __name__ == "__main__":
    main()
