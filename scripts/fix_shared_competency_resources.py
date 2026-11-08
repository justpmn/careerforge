
"""
Repair safe URL aliases and reuse common learning resources.

Dry run by default.
Run with --apply to write changes.

Does not invent resource URLs or modify career profiles.
"""

import argparse
import json

from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

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

SHARED_RESOURCES = {
    "version_control": "Pro Git",
    "containers": "Docker Getting Started",
    "ci_cd": "GitHub Actions Getting Started",
}

TARGET_CAREERS = {
    "frontend_developer",
    "full_stack_developer",
    "cloud_engineer",
    "devops_sre",
}


def normalized_url(url: str) -> tuple:
    """Normalize only nonessential URL differences."""

    parsed = urlsplit(url.strip())

    return (
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        parsed.query,
    )


def coverage(catalog: dict) -> tuple[int, int]:
    valid_urls = {
        resource["url"]
        for resource in catalog["resources"]
    }

    mapped = defaultdict(set)

    for mapping in catalog["mappings"]:
        mapped[
            (mapping["career_key"], mapping["competency_key"])
        ].update(mapping.get("urls", []))

    total = 0
    covered = 0

    for career_key, competencies in (
        CAREER_COMPETENCY_PROFILES.items()
    ):
        for competency in competencies:
            total += 1

            urls = mapped[
                (career_key, competency["key"])
            ]

            if urls.intersection(valid_urls):
                covered += 1

    return covered, total


def fix_catalog(apply: bool = False) -> None:
    original = CATALOG_PATH.read_text(encoding="utf-8")
    catalog = json.loads(original)

    resources = catalog["resources"]
    mappings = catalog["mappings"]

    valid_urls = {
        resource["url"]
        for resource in resources
    }

    aliases = defaultdict(set)
    by_title = defaultdict(list)

    for resource in resources:
        url = resource["url"]
        title = resource["title"]

        aliases[normalized_url(url)].add(url)
        by_title[title.casefold()].append(url)

    before_covered, total = coverage(catalog)

    repaired = []
    additions = []
    unresolved = []

    # Repair URLs only when a unique resource definition
    # matches after conservative normalization.

    for mapping in mappings:
        updated_urls = []

        for url in mapping.get("urls", []):
            if url in valid_urls:
                updated_urls.append(url)
                continue

            candidates = aliases.get(
                normalized_url(url),
                set(),
            )

            if len(candidates) == 1:
                replacement = next(iter(candidates))

                updated_urls.append(replacement)

                repaired.append((
                    mapping["career_key"],
                    mapping["competency_key"],
                    url,
                    replacement,
                ))
            else:
                updated_urls.append(url)

        mapping["urls"] = updated_urls

    # Reuse well-established general resources.
    # Only fill competencies that currently have
    # no resolvable learning resource.

    for career_key in sorted(TARGET_CAREERS):
        competencies = CAREER_COMPETENCY_PROFILES[
            career_key
        ]

        profile_keys = {
            competency["key"]
            for competency in competencies
        }

        for competency_key, title in (
            SHARED_RESOURCES.items()
        ):
            if competency_key not in profile_keys:
                continue

            candidates = by_title.get(
                title.casefold(),
                [],
            )

            if len(candidates) != 1:
                print(
                    f"SKIPPED: {title} "
                    "(missing or ambiguous resource)"
                )
                continue

            url = candidates[0]

            matches = [
                item
                for item in mappings
                if item["career_key"] == career_key
                and item["competency_key"] == competency_key
            ]

            existing_valid = any(
                mapped_url in valid_urls
                for mapping in matches
                for mapped_url in mapping.get("urls", [])
            )

            if existing_valid:
                continue

            if matches:
                if url not in matches[0].get("urls", []):
                    matches[0].setdefault(
                        "urls", []
                    ).append(url)
            else:
                mappings.append({
                    "career_key": career_key,
                    "competency_key": competency_key,
                    "urls": [url],
                })

            additions.append((
                career_key,
                competency_key,
                title,
            ))

    # Report references that still lack definitions.

    for mapping in mappings:
        for url in mapping.get("urls", []):
            if url not in valid_urls:
                unresolved.append((
                    mapping["career_key"],
                    mapping["competency_key"],
                    url,
                ))

    after_covered, _ = coverage(catalog)

    print("\nCOMPETENCY CATALOG REPAIR")
    print("=" * 65)

    print("Coverage before:", f"{before_covered}/{total}")
    print("Coverage after:", f"{after_covered}/{total}")
    print("Safe URL repairs:", len(repaired))
    print("Shared resource assignments:", len(additions))
    print("Unresolved URL references:", len(unresolved))

    if repaired:
        print("\nURL REPAIRS")
        for career, key, old, new in repaired:
            print(f"  {career} / {key}")
            print(f"    Old: {old}")
            print(f"    New: {new}")

    if additions:
        print("\nNEW SHARED MAPPINGS")
        for career, key, title in additions:
            print(f"  {career} / {key}: {title}")

    if unresolved:
        print("\nREFERENCES REQUIRING REVIEW")
        for career, key, url in unresolved:
            print(f"  {career} / {key}")
            print(f"    {url}")

    if not apply:
        print("\nDRY RUN: no changes written.")
        return

    if not repaired and not additions:
        print("\nNo changes necessary.")
        return

    CATALOG_PATH.write_text(
        json.dumps(
            catalog,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    print("\nCatalog updated successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write approved catalog repairs.",
    )

    args = parser.parse_args()

    fix_catalog(apply=args.apply)
