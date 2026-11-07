
"""
Register existing learning-resource URLs that are referenced
by competency mappings but missing from the resource catalog.

Dry run by default.
Use --apply to write changes.

This script does not:
- Modify existing mappings
- Delete existing resources
- Change career competency profiles
- Access the database
"""

import argparse
import json

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


# Metadata for the 15 verified documentation URLs.
# Each tuple contains:
# (URL, title, provider, resource_type, description)

RESOURCE_DEFINITIONS = [
    (
        "https://stat.ethz.ch/CRAN/doc/manuals/r-release/R-intro.html",
        "An Introduction to R",
        "R Core Team",
        "documentation",
        "Introduction to R programming, data structures, statistical computing and graphics.",
    ),
    (
        "https://pandas.pydata.org/docs/getting_started/",
        "Getting Started with pandas",
        "pandas",
        "tutorial",
        "Learn data manipulation, DataFrames, cleaning, transformation and analysis.",
    ),
    (
        "https://scikit-learn.org/stable/getting_started",
        "Getting Started with scikit-learn",
        "scikit-learn",
        "tutorial",
        "Introduction to machine learning estimators, preprocessing, training and model evaluation.",
    ),
    (
        "https://numpy.org/doc/stable/user/absolute_beginners",
        "NumPy: The Absolute Basics for Beginners",
        "NumPy",
        "tutorial",
        "Learn numerical arrays, array operations and scientific computing foundations.",
    ),
    (
        "https://jupyter.org/try",
        "Try Jupyter",
        "Project Jupyter",
        "interactive",
        "Explore interactive notebooks and computational environments in the browser.",
    ),
    (
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "JavaScript Guide",
        "MDN Web Docs",
        "documentation",
        "Learn JavaScript syntax, functions, objects, asynchronous programming and language fundamentals.",
    ),
    (
        "https://nodejs.org/learn/getting-started/introduction-to-nodejs",
        "Introduction to Node.js",
        "Node.js",
        "tutorial",
        "Introduction to JavaScript server-side development with Node.js.",
    ),
    (
        "https://dev.mysql.com/doc/mysql-getting-started/en/",
        "Getting Started with MySQL",
        "MySQL",
        "documentation",
        "Learn relational database setup, SQL queries and fundamental MySQL operations.",
    ),
    (
        "https://vitest.dev/guide/",
        "Getting Started with Vitest",
        "Vitest",
        "tutorial",
        "Introduction to automated JavaScript and TypeScript testing with Vitest.",
    ),
    (
        "https://dev.java/learn/",
        "Java Learning Tutorials",
        "Dev.java",
        "tutorial",
        "Learn Java programming fundamentals, object-oriented programming and core APIs.",
    ),
    (
        "https://docs.snowflake.com/en/user-guide-getting-started",
        "Getting Started with Snowflake",
        "Snowflake",
        "documentation",
        "Introduction to Snowflake cloud data warehousing, storage and querying.",
    ),
    (
        "https://docs.cloud.google.com/bigquery/docs/",
        "BigQuery Documentation",
        "Google Cloud",
        "documentation",
        "Learn cloud analytics, BigQuery data warehousing and SQL-based data processing.",
    ),
    (
        "https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/GettingStarted.html",
        "Getting Started with AWS CloudFormation",
        "Amazon Web Services",
        "tutorial",
        "Learn how to provision and manage cloud infrastructure using CloudFormation templates.",
    ),
    (
        "https://developer.hashicorp.com/terraform/tutorials/aws-get-started",
        "Terraform AWS Tutorials",
        "HashiCorp",
        "tutorial",
        "Learn infrastructure as code by provisioning and managing AWS resources with Terraform.",
    ),
    (
        "https://docs.ansible.com/projects/ansible/latest/getting_started/index.html",
        "Getting Started with Ansible",
        "Ansible",
        "tutorial",
        "Learn configuration management, infrastructure automation and Ansible playbooks.",
    ),
]


def register_missing_resources(apply: bool = False) -> None:
    catalog = json.loads(
        CATALOG_PATH.read_text(encoding="utf-8")
    )

    resources = catalog["resources"]
    mappings = catalog["mappings"]

    existing_urls = {
        resource["url"]
        for resource in resources
    }

    if len(existing_urls) != len(resources):
        raise ValueError(
            "Duplicate resource URLs already exist in the catalog."
        )

    referenced_urls = {
        url
        for mapping in mappings
        for url in mapping.get("urls", [])
    }

    missing_urls = sorted(
        referenced_urls - existing_urls
    )

    metadata = {}

    for (
        url,
        title,
        provider,
        resource_type,
        description,
    ) in RESOURCE_DEFINITIONS:

        if url in metadata:
            raise ValueError(
                f"Duplicate metadata definition: {url}"
            )

        metadata[url] = {
            "title": title,
            "provider": provider,
            "resource_type": resource_type,
            "url": url,
            "description": description,
        }

    undefined_urls = [
        url
        for url in missing_urls
        if url not in metadata
    ]

    print("\nCAREERFORGE RESOURCE REGISTRATION")
    print("=" * 65)

    print("Registered resources:", len(resources))
    print("Mapping records:", len(mappings))
    print("Missing unique URLs:", len(missing_urls))

    if undefined_urls:
        print("\nUNRECOGNIZED URL REFERENCES")

        for url in undefined_urls:
            print(" -", url)

        raise ValueError(
            "Missing URLs require reviewed metadata before registration."
        )

    additions = [
        metadata[url]
        for url in missing_urls
    ]

    for resource in additions:
        print(
            f"\n+ {resource['title']}"
            f"\n  Provider: {resource['provider']}"
            f"\n  URL: {resource['url']}"
        )

    if not apply:
        print("\nDRY RUN: no files modified.")
        print("Proposed additions:", len(additions))
        return

    if not additions:
        print("\nCatalog already contains all referenced URLs.")
        return

    resources.extend(additions)

    CATALOG_PATH.write_text(
        json.dumps(
            catalog,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    print("\nResource definitions registered successfully.")
    print("Total resources:", len(resources))
    print(
        "Career profiles:",
        len(CAREER_COMPETENCY_PROFILES),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write missing resource definitions to the catalog.",
    )

    args = parser.parse_args()

    register_missing_resources(
        apply=args.apply
    )
