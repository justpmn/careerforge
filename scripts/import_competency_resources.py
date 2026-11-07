
import argparse
import json

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings
from src.backend.app.database.models.competency_resource_link import (
    CompetencyResourceLink,
)
from src.backend.app.database.models.learning_resource import LearningResource
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)
from src.backend.app.services.learning_resource_service import (
    CATALOG_PATH,
    CAREER_COMPETENCY_RESOURCE_URLS,
    COMMON_COMPETENCY_RESOURCE_URLS,
)


def load_source_data():
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    if catalog.get("version") != 1:
        raise ValueError("Unsupported resource catalog version.")

    definitions = {}

    for item in catalog["resources"]:
        url = item["url"]

        if url in definitions:
            raise ValueError(f"Duplicate resource URL: {url}")

        definitions[url] = item

    mappings = {}

    for item in catalog["mappings"]:
        key = (item["career_key"], item["competency_key"])

        if key in mappings:
            raise ValueError(f"Duplicate competency mapping: {key}")

        mappings[key] = list(dict.fromkeys(item["urls"]))

    fallback_count = 0

    for career_key, competencies in CAREER_COMPETENCY_PROFILES.items():
        for competency in competencies:
            competency_key = competency["key"]
            key = (career_key, competency_key)

            if key in mappings:
                continue

            urls = CAREER_COMPETENCY_RESOURCE_URLS.get(
                key,
                COMMON_COMPETENCY_RESOURCE_URLS.get(
                    competency_key, []
                ),
            )

            if urls:
                mappings[key] = list(dict.fromkeys(urls))
                fallback_count += 1

    return definitions, mappings, fallback_count


def import_resources(db: Session, definitions: dict):
    resources = db.scalars(select(LearningResource)).all()
    by_url = {}

    for resource in resources:
        if resource.url in by_url:
            raise ValueError(
                f"Duplicate database resource URL: {resource.url}"
            )

        by_url[resource.url] = resource

    created = 0

    for url, item in definitions.items():
        if url in by_url:
            continue

        resource = LearningResource(
            title=item["title"],
            provider=item.get("provider"),
            resource_type=item.get("resource_type") or "resource",
            url=url,
            description=item.get("description"),
        )

        db.add(resource)
        by_url[url] = resource
        created += 1

    db.flush()
    return by_url, created


def import_mappings(
    db: Session,
    mappings: dict,
    resources_by_url: dict,
):
    existing = set(
        db.execute(
            select(
                CompetencyResourceLink.career_key,
                CompetencyResourceLink.competency_key,
                CompetencyResourceLink.resource_id,
            )
        ).all()
    )

    missing_urls = sorted({
        url
        for urls in mappings.values()
        for url in urls
        if url not in resources_by_url
    })

    if missing_urls:
        print("\nMissing resource definitions:")
        for url in missing_urls:
            print(f" - {url}")

        raise ValueError(
            "Some mappings reference resources not found in "
            "PostgreSQL or the JSON resource definitions."
        )

    created = 0

    for (career_key, competency_key), urls in mappings.items():
        for url in urls:
            resource = resources_by_url[url]
            key = (career_key, competency_key, resource.id)

            if key in existing:
                continue

            db.add(
                CompetencyResourceLink(
                    career_key=career_key,
                    competency_key=competency_key,
                    resource_id=resource.id,
                )
            )

            existing.add(key)
            created += 1

    return created


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit the imported resources and mappings.",
    )
    args = parser.parse_args()

    definitions, mappings, fallback_count = load_source_data()
    engine = create_engine(settings.database_url)

    try:
        with Session(engine) as db:
            database = db.scalar(text("SELECT current_database()"))

            if database != "careerforge":
                raise SystemExit(
                    "This importer only targets the CareerForge "
                    "development database."
                )

            resources_by_url, new_resources = import_resources(
                db, definitions
            )

            new_links = import_mappings(
                db, mappings, resources_by_url
            )

            print("\nCAREERFORGE RESOURCE IMPORT")
            print("---------------------------")
            print(f"Catalog definitions: {len(definitions)}")
            print(f"Career/competency mappings: {len(mappings)}")
            print(f"Fallback mappings included: {fallback_count}")
            print(f"New resources: {new_resources}")
            print(f"New competency links: {new_links}")

            if args.apply:
                db.commit()
                print("\nImport committed successfully.")
            else:
                db.rollback()
                print("\nPreview only. No changes saved.")
                print("Run with --apply to commit.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
