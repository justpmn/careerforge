
"""
Seed learning and competency resources into careerforge_test only.

Reuses existing CareerForge resource definitions.
Does not modify the development database.

Safe to rerun.
"""

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from src.backend.app.core.config import settings


TEST_DATABASE = "careerforge_test"


def get_test_database_url():
    source_url = make_url(settings.database_url)

    if source_url.drivername != "postgresql+psycopg":
        raise RuntimeError(
            "Expected PostgreSQL using psycopg."
        )

    if source_url.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise RuntimeError(
            "Only local PostgreSQL connections are allowed."
        )

    if source_url.port not in {None, 5432}:
        raise RuntimeError(
            "Unexpected PostgreSQL port."
        )

    if source_url.database not in {
        "careerforge",
        TEST_DATABASE,
    }:
        raise RuntimeError(
            "Unexpected source database."
        )

    return source_url.set(database=TEST_DATABASE)


def main():
    test_url = get_test_database_url()

    engine = create_engine(
        test_url,
        pool_pre_ping=True,
    )

    try:
        # Confirm the actual connected database before writes.
        with engine.connect() as connection:
            database_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        if database_name != TEST_DATABASE:
            raise RuntimeError(
                "Integration database safety check failed."
            )

        from scripts.seed_learning_resources import (
            seed_learning_resources,
        )

        from scripts.seed_competency_resources import (
            load_catalog,
        )

        from src.backend.app.database.models.learning_resource import (
            LearningResource,
        )

        from src.backend.app.database.models.learning_resource_skill import (
            LearningResourceSkill,
        )

        from src.backend.app.services.learning_resource_service import (
            get_resources_for_competencies,
        )

        from src.backend.app.services.career_competency_profiles import (
            CAREER_COMPETENCY_PROFILES,
        )

        print("=" * 55)
        print("CAREERFORGE INTEGRATION RESOURCE SEEDING")
        print("=" * 55)
        print(f"Target database: {database_name}")

        # Load and validate the original JSON catalog.
        catalog = load_catalog()

        resource_definitions = catalog["resources"]
        competency_mappings = catalog["mappings"]

        resource_urls = [
            item["url"]
            for item in resource_definitions
        ]

        if len(resource_urls) != len(set(resource_urls)):
            raise ValueError(
                "Duplicate resource URLs in competency catalog."
            )

        mapping_keys = [
            (item["career_key"], item["competency_key"])
            for item in competency_mappings
        ]

        if len(mapping_keys) != len(set(mapping_keys)):
            raise ValueError(
                "Duplicate career-competency mappings."
            )

        required_urls = {
            url
            for item in competency_mappings
            for url in item["urls"]
        }

        with Session(engine) as db:
            # Everything succeeds together or rolls back.
            with db.begin():

                print("\n[1/3] Seeding curated learning resources...")

                seed_learning_resources(db)

                # Includes resources inserted above.
                existing_urls = set(
                    db.scalars(
                        select(LearningResource.url)
                    ).all()
                )

                available_urls = (
                    existing_urls | set(resource_urls)
                )

                missing_definitions = (
                    required_urls - available_urls
                )

                if missing_definitions:
                    raise ValueError(
                        "Missing resource definitions:\n"
                        + "\n".join(
                            sorted(missing_definitions)
                        )
                    )

                print(
                    "\n[2/3] Seeding competency resources..."
                )

                added = 0
                skipped = 0

                for item in resource_definitions:

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

                    existing_urls.add(item["url"])
                    added += 1

                db.flush()

                stored_urls = set(
                    db.scalars(
                        select(LearningResource.url)
                    ).all()
                )

                unresolved_urls = (
                    required_urls - stored_urls
                )

                if unresolved_urls:
                    raise ValueError(
                        "Unresolved competency resource URLs:\n"
                        + "\n".join(sorted(unresolved_urls))
                    )

                print(f"Competency resources added: {added}")
                print(f"Existing resources skipped: {skipped}")

                print(
                    "\n[3/3] Validating Data Engineer mappings..."
                )

                profile = CAREER_COMPETENCY_PROFILES[
                    "data_engineer"
                ]

                competency_keys = [
                    group["key"]
                    for group in profile
                ]

                resolved = get_resources_for_competencies(
                    db=db,
                    competency_keys=competency_keys,
                    career_key="data_engineer",
                )

                if set(resolved) != set(competency_keys):
                    raise RuntimeError(
                        "Incomplete Data Engineer resource mapping."
                    )

                print(
                    "Data Engineer competency resource "
                    "resolution: PASS"
                )

        # Read committed records in a separate session.
        with Session(engine) as db:
            resource_count = db.scalar(
                select(func.count()).select_from(
                    LearningResource
                )
            )

            link_count = db.scalar(
                select(func.count()).select_from(
                    LearningResourceSkill
                )
            )

        if not resource_count or not link_count:
            raise RuntimeError(
                "Learning-resource catalog remains incomplete."
            )

        print("\n" + "=" * 55)
        print("INTEGRATION RESOURCE CATALOG")
        print("=" * 55)
        print(f"Database: {TEST_DATABASE}")
        print(f"Learning resources: {resource_count}")
        print(f"Skill-resource links: {link_count}")
        print(
            "JSON competency mappings: "
            f"{len(competency_mappings)}"
        )
        print("Resource validation: PASS")
        print("Development database: untouched")
        print("=" * 55)

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
