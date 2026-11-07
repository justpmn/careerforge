
"""
Audit competency learning-resource coverage across
all CareerForge career profiles.

Read-only: does not modify the catalog or database.
"""

import argparse
import json

from collections import defaultdict
from pathlib import Path

from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)


ROOT = Path(__file__).resolve().parents[1]

CATALOG_PATH = (
    ROOT
    / "src"
    / "backend"
    / "app"
    / "resource_catalog"
    / "competency_resources.json"
)


def load_catalog():
    with CATALOG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def audit(selected_career=None):
    catalog = load_catalog()

    resources = catalog["resources"]
    mappings = catalog["mappings"]

    resource_index = {
        resource["url"]: resource
        for resource in resources
        if isinstance(resource, dict)
        and isinstance(resource.get("url"), str)
    }

    mapping_index = defaultdict(list)
    cross_career_index = defaultdict(list)

    invalid_references = []
    unknown_competencies = []
    referenced_urls = set()

    for mapping in mappings:
        career_key = mapping["career_key"]
        competency_key = mapping["competency_key"]

        urls = mapping.get("urls") or []

        mapping_index[
            (career_key, competency_key)
        ].extend(urls)

        for url in urls:
            referenced_urls.add(url)

            if url not in resource_index:
                invalid_references.append(
                    (career_key, competency_key, url)
                )
            else:
                cross_career_index[
                    competency_key
                ].append((career_key, url))

        profile_keys = {
            item["key"]
            for item in CAREER_COMPETENCY_PROFILES.get(
                career_key, []
            )
        }

        if competency_key not in profile_keys:
            unknown_competencies.append(
                (career_key, competency_key)
            )

    total_competencies = 0
    total_covered = 0

    print("\nCAREERFORGE COMPETENCY RESOURCE AUDIT")
    print("=" * 72)

    print(f"Career profiles: {len(CAREER_COMPETENCY_PROFILES)}")
    print(f"Catalog resources: {len(resources)}")
    print(f"Mapping records: {len(mappings)}")
    print(f"Indexed resource URLs: {len(resource_index)}")

    print("\nCAREER COVERAGE")
    print("-" * 72)

    print(
        f"{'Career':27}"
        f"{'Total':>7}"
        f"{'Covered':>10}"
        f"{'Missing':>10}"
        f"{'Coverage':>12}"
    )

    print("-" * 72)

    for career_key, competencies in sorted(
        CAREER_COMPETENCY_PROFILES.items()
    ):
        total = len(competencies)
        covered = 0

        for competency in competencies:
            urls = mapping_index.get(
                (career_key, competency["key"]),
                [],
            )

            valid_urls = {
                url
                for url in urls
                if url in resource_index
            }

            if valid_urls:
                covered += 1

        missing = total - covered
        percentage = (
            (covered / total) * 100
            if total
            else 0
        )

        total_competencies += total
        total_covered += covered

        print(
            f"{career_key:27}"
            f"{total:>7}"
            f"{covered:>10}"
            f"{missing:>10}"
            f"{percentage:>11.1f}%"
        )

    print("-" * 72)

    overall = (
        total_covered / total_competencies * 100
        if total_competencies
        else 0
    )

    print(
        f"\nOverall: {total_covered}/"
        f"{total_competencies} competencies covered "
        f"({overall:.1f}%)"
    )

    print(
        "Missing competencies:",
        total_competencies - total_covered,
    )

    print(
        "Unused resource definitions:",
        len(set(resource_index) - referenced_urls),
    )

    print(
        "Invalid resource URL references:",
        len(invalid_references),
    )

    print(
        "Mappings to unknown competencies:",
        len(unknown_competencies),
    )

    if invalid_references:
        print("\nINVALID RESOURCE REFERENCES")

        for career, competency, url in (
            invalid_references[:15]
        ):
            print(f"  {career} / {competency}: {url}")

    if unknown_competencies:
        print("\nUNKNOWN COMPETENCY KEYS")

        for career, competency in (
            unknown_competencies[:15]
        ):
            print(f"  {career}: {competency}")

    if selected_career:
        if selected_career not in CAREER_COMPETENCY_PROFILES:
            raise ValueError(
                f"Unknown career: {selected_career}"
            )

        print(
            f"\nMISSING RESOURCES: {selected_career}"
        )
        print("=" * 72)

        for competency in (
            CAREER_COMPETENCY_PROFILES[selected_career]
        ):
            key = competency["key"]

            urls = mapping_index.get(
                (selected_career, key),
                [],
            )

            valid_urls = {
                url
                for url in urls
                if url in resource_index
            }

            if valid_urls:
                continue

            print(
                f"\n- {competency['name']} [{key}]"
            )

            candidates = {
                (other_career, url)
                for other_career, url
                in cross_career_index.get(key, [])
                if other_career != selected_career
            }

            if candidates:
                print(
                    "  Existing mappings with the same "
                    "competency key:"
                )

                for other_career, url in sorted(
                    candidates
                )[:5]:
                    resource = resource_index[url]

                    print(
                        f"  * {other_career}: "
                        f"{resource.get('title', url)}"
                    )
            else:
                print(
                    "  No exact-key reuse candidates found."
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--career",
        default=None,
        help="Show uncovered competencies for one career.",
    )

    args = parser.parse_args()

    audit(selected_career=args.career)
