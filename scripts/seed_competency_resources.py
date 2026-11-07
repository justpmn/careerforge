
import json
from pathlib import Path

from sqlalchemy import select

from src.backend.app.database.session import SessionLocal
from src.backend.app.database.models.learning_resource import (
    LearningResource,
)


CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "backend"
    / "app"
    / "resource_catalog"
    / "competency_resources.json"
)


def load_catalog() -> dict:
    with CATALOG_PATH.open("r", encoding="utf-8") as file:
        catalog = json.load(file)

    if catalog.get("version") != 1:
        raise ValueError("Unsupported resource catalog version.")

    resources = catalog.get("resources")
    mappings = catalog.get("mappings")

    if not isinstance(resources, list):
        raise ValueError("Catalog resources must be a list.")

    if not isinstance(mappings, list):
        raise ValueError("Catalog mappings must be a list.")

    return catalog


def seed_competency_resources() -> None:
    catalog = load_catalog()

    resources = catalog["resources"]
    mappings = catalog["mappings"]

    # Ensure no resource URL appears twice in the seed data.
    resource_urls = [item["url"] for item in resources]

    if len(resource_urls) != len(set(resource_urls)):
        raise ValueError(
            "Duplicate resource URLs found in the catalog."
        )

    # Each career and competency pair should be unique.
    mapping_keys = [
        (item["career_key"], item["competency_key"])
        for item in mappings
    ]

    if len(mapping_keys) != len(set(mapping_keys)):
        raise ValueError(
            "Duplicate career-competency mappings found."
        )

    # Collect all URLs used by competency mappings.
    required_urls = {
        url
        for mapping in mappings
        for url in mapping["urls"]
    }

    with SessionLocal() as db:
        try:
            # Find resources already stored in PostgreSQL.
            existing_urls = set(
                db.scalars(
                    select(LearningResource.url).where(
                        LearningResource.url.in_(
                            required_urls | set(resource_urls)
                        )
                    )
                ).all()
            )

            # Every mapping must reference either an existing
            # database resource or a new catalog resource.
            available_urls = existing_urls | set(resource_urls)

            missing_urls = required_urls - available_urls

            if missing_urls:
                raise ValueError(
                    "Mapped resources are missing from both "
                    "the database and the seed catalog:\n"
                    + "\n".join(sorted(missing_urls))
                )

            added = 0
            skipped = 0

            for item in resources:
                if item["url"] in existing_urls:
                    skipped += 1
                    continue

                db.add(
                    LearningResource(
                        title=item["title"],
                        provider=item["provider"],
                        resource_type=item["resource_type"],
                        url=item["url"],
                        description=item["description"],
                    )
                )

                added += 1

            db.flush()

            # Confirm that all mapped URLs now exist.
            stored_urls = set(
                db.scalars(
                    select(LearningResource.url).where(
                        LearningResource.url.in_(required_urls)
                    )
                ).all()
            )

            still_missing = required_urls - stored_urls

            if still_missing:
                raise ValueError(
                    "Mapped resources not found in PostgreSQL:\n"
                    + "\n".join(sorted(still_missing))
                    + "\nRun the existing learning resource "
                      "seeder first."
                )

            db.commit()

            print("\nCOMPETENCY RESOURCE SEEDING")
            print("=" * 45)
            print(f"Resources inserted: {added}")
            print(f"Existing resources skipped: {skipped}")
            print(f"Competency mappings: {len(mappings)}")
            print(f"Referenced resources available: {len(stored_urls)}")
            print("\nSeeding completed successfully.")

        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    seed_competency_resources()
