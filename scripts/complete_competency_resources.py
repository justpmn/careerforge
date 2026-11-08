
"""
Complete CareerForge's competency learning-resource catalog.

- Uses official learning resources
- Reuses already registered URLs
- Adds missing resource definitions
- Adds only uncovered competency mappings
- Validates all 22 career profiles
- Safe to run repeatedly
- Dry run by default
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
    / "src/backend/app/resource_catalog/competency_resources.json"
)


# Format:
# alias: (URL, title, provider, type, description)
#
# Entries already present in the catalog are reused
# without overwriting their existing metadata.

RESOURCES = {
    "javascript": (
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "JavaScript Guide",
        "MDN Web Docs",
        "documentation",
        "JavaScript language fundamentals and programming concepts.",
    ),
    "html_css": (
        "https://developer.mozilla.org/en-US/docs/Learn_web_development/Getting_started/Your_first_website",
        "Your First Website",
        "MDN Web Docs",
        "tutorial",
        "Learn HTML structure, CSS styling and basic web development.",
    ),
    "react": (
        "https://react.dev/learn",
        "Learn React",
        "React",
        "tutorial",
        "Learn React components, JSX, state, events and rendering.",
    ),
    "vite": (
        "https://vite.dev/guide/",
        "Getting Started with Vite",
        "Vite",
        "documentation",
        "Learn frontend project scaffolding, development servers and builds.",
    ),
    "vitest": (
        "https://vitest.dev/guide/",
        "Getting Started with Vitest",
        "Vitest",
        "tutorial",
        "Learn automated testing for JavaScript and TypeScript applications.",
    ),
    "pytest": (
        "https://docs.pytest.org/en/stable/getting-started.html",
        "Getting Started with pytest",
        "pytest",
        "tutorial",
        "Learn Python testing, assertions and running automated tests.",
    ),
    "fastapi": (
        "https://fastapi.tiangolo.com/tutorial/",
        "FastAPI Tutorial",
        "FastAPI",
        "tutorial",
        "Learn Python backend services and REST API implementation.",
    ),
    "nodejs": (
        "https://nodejs.org/learn/getting-started/introduction-to-nodejs",
        "Introduction to Node.js",
        "Node.js",
        "tutorial",
        "Learn server-side JavaScript with the Node.js runtime.",
    ),
    "postgresql": (
        "https://www.postgresql.org/docs/current/tutorial.html",
        "PostgreSQL Tutorial",
        "PostgreSQL",
        "documentation",
        "Learn relational databases, SQL queries and database operations.",
    ),
    "mysql": (
        "https://dev.mysql.com/doc/mysql-getting-started/en/",
        "Getting Started with MySQL",
        "MySQL",
        "documentation",
        "Learn MySQL setup, database operations and SQL foundations.",
    ),
    "http": (
        "https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview",
        "Overview of HTTP",
        "MDN Web Docs",
        "documentation",
        "Learn HTTP requests, responses and client-server communication.",
    ),
    "azure": (
        "https://learn.microsoft.com/en-us/training/paths/microsoft-azure-fundamentals-describe-cloud-concepts/",
        "Azure Fundamentals: Cloud Concepts",
        "Microsoft Learn",
        "course",
        "Understand cloud platforms, service models and Azure fundamentals.",
    ),
    "terraform": (
        "https://developer.hashicorp.com/terraform/tutorials/aws-get-started",
        "Terraform AWS Tutorials",
        "HashiCorp",
        "tutorial",
        "Learn infrastructure provisioning and infrastructure as code.",
    ),
    "kubernetes": (
        "https://kubernetes.io/docs/tutorials/kubernetes-basics/index.html",
        "Learn Kubernetes Basics",
        "Kubernetes",
        "tutorial",
        "Learn container orchestration, deployments, scaling and updates.",
    ),
    "python": (
        "https://docs.python.org/3/tutorial/",
        "The Python Tutorial",
        "Python Software Foundation",
        "tutorial",
        "Learn Python programming and foundations for automation scripts.",
    ),
    "powershell": (
        "https://learn.microsoft.com/powershell/scripting/learn/ps101/00-introduction",
        "PowerShell 101",
        "Microsoft Learn",
        "tutorial",
        "Learn PowerShell scripting and system administration automation.",
    ),
    "sentinel": (
        "https://learn.microsoft.com/azure/sentinel/quickstart-onboard",
        "Getting Started with Microsoft Sentinel",
        "Microsoft Learn",
        "tutorial",
        "Learn SIEM onboarding, security event ingestion and monitoring. Azure subscription may be required.",
    ),
    "firewall": (
        "https://docs.netgate.com/pfsense/en/latest/firewall/index.html",
        "pfSense Firewall Documentation",
        "Netgate",
        "documentation",
        "Learn firewall configuration, traffic filtering and firewall rules.",
    ),
    "linux": (
        "https://ubuntu.com/desktop/docs/en/latest/tutorial/the-linux-command-line-for-beginners/",
        "Linux Command Line for Beginners",
        "Ubuntu",
        "tutorial",
        "Learn Linux command-line navigation, commands and administration basics.",
    ),
    "prometheus": (
        "https://prometheus.io/docs/prometheus/latest/getting_started/",
        "Getting Started with Prometheus",
        "Prometheus",
        "tutorial",
        "Learn metric collection, monitoring targets and time-series queries.",
    ),
    "grafana": (
        "https://grafana.com/tutorials/grafana-fundamentals/",
        "Grafana Fundamentals",
        "Grafana Labs",
        "tutorial",
        "Learn observability dashboards and monitoring visualizations.",
    ),
    "ansible": (
        "https://docs.ansible.com/projects/ansible/latest/getting_started/index.html",
        "Getting Started with Ansible",
        "Ansible",
        "tutorial",
        "Learn configuration management, playbooks and infrastructure automation.",
    ),
}


# Explicit, reviewed assignments for the 27 gaps.
# Each competency may point to one or multiple resources.

ASSIGNMENTS = {
    "cloud_engineer": {
        "cloud_platform_familiarity": ["azure"],
        "iac_tooling": ["terraform"],
        "orchestration_tooling": ["kubernetes"],
        "automation_scripting": ["python", "powershell"],
    },
    "cybersecurity_analyst": {
        "siem_tooling": ["sentinel"],
        "firewall_tooling": ["firewall"],
        "security_scripting": ["python", "powershell"],
        "security_os": ["linux"],
        "cloud_platform": ["azure"],
    },
    "devops_sre": {
        "automation_scripting": ["python", "powershell"],
        "iac_tooling": ["terraform"],
        "orchestration_tooling": ["kubernetes"],
        "observability_tooling": ["prometheus", "grafana"],
        "automation_platforms": ["ansible"],
        "cloud_platform": ["azure"],
    },
    "frontend_developer": {
        "web_programming": ["javascript"],
        "web_fundamentals": ["html_css"],
        "frontend_framework": ["react"],
        "build_tools": ["vite"],
        "testing": ["vitest"],
    },
    "full_stack_developer": {
        "web_programming": ["javascript"],
        "web_fundamentals": ["html_css"],
        "frontend_framework": ["react"],
        "backend_runtime": ["fastapi", "nodejs"],
        "database": ["postgresql", "mysql"],
        "api": ["fastapi", "http"],
        "testing": ["pytest", "vitest"],
    },
}


def get_missing(catalog):
    valid_urls = {
        resource["url"]
        for resource in catalog["resources"]
    }

    covered = set()

    for mapping in catalog["mappings"]:
        if any(
            url in valid_urls
            for url in mapping.get("urls", [])
        ):
            covered.add((
                mapping["career_key"],
                mapping["competency_key"],
            ))

    missing = set()

    for career_key, competencies in (
        CAREER_COMPETENCY_PROFILES.items()
    ):
        for competency in competencies:
            pair = (career_key, competency["key"])

            if pair not in covered:
                missing.add(pair)

    return missing


def complete_catalog(apply=False):
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
            "Duplicate resource definitions detected."
        )

    planned = {
        (career, key)
        for career, competencies in ASSIGNMENTS.items()
        for key in competencies
    }

    # All planned keys must exist in the real profiles.
    for career, key in planned:
        actual_keys = {
            item["key"]
            for item in CAREER_COMPETENCY_PROFILES.get(
                career, []
            )
        }

        if key not in actual_keys:
            raise ValueError(
                f"Invalid competency: {career}/{key}"
            )

    for career, competencies in ASSIGNMENTS.items():
        for key, aliases in competencies.items():
            if not aliases:
                raise ValueError(
                    f"No resources for {career}/{key}"
                )

            for alias in aliases:
                if alias not in RESOURCES:
                    raise ValueError(
                        f"Unknown resource alias: {alias}"
                    )

    before = get_missing(catalog)

    unexpected = before - planned

    if unexpected:
        raise ValueError(
            "Unplanned competency gaps detected: "
            + repr(sorted(unexpected))
        )

    new_definitions = []
    new_mappings = []

    # Register only resources actually required by
    # competencies that are still uncovered.

    required_aliases = {
        alias
        for career, key in before
        for alias in ASSIGNMENTS[career][key]
    }

    for alias in sorted(required_aliases):
        (
            url,
            title,
            provider,
            resource_type,
            description,
        ) = RESOURCES[alias]

        if url in existing_urls:
            continue

        resources.append({
            "title": title,
            "provider": provider,
            "resource_type": resource_type,
            "url": url,
            "description": description,
        })

        existing_urls.add(url)
        new_definitions.append(title)

    # Create exactly one new mapping per uncovered
    # competency, with all selected resource URLs.

    for career, key in sorted(before):
        urls = list(dict.fromkeys(
            RESOURCES[alias][0]
            for alias in ASSIGNMENTS[career][key]
        ))

        # Preserve existing mappings if one already
        # exists but has no valid resource URLs.
        existing_mapping = next(
            (
                item
                for item in mappings
                if item["career_key"] == career
                and item["competency_key"] == key
            ),
            None,
        )

        if existing_mapping is not None:
            existing_mapping["urls"] = list(
                dict.fromkeys(
                    existing_mapping.get("urls", [])
                    + urls
                )
            )
        else:
            mappings.append({
                "career_key": career,
                "competency_key": key,
                "urls": urls,
            })

        new_mappings.append((career, key, urls))

    after = get_missing(catalog)

    # Refuse to save an incomplete or inconsistent catalog.
    if after:
        raise ValueError(
            f"Uncovered competencies remain: {sorted(after)}"
        )

    dangling = {
        url
        for mapping in mappings
        for url in mapping.get("urls", [])
        if url not in existing_urls
    }

    if dangling:
        raise ValueError(
            f"Unregistered resource URLs: {sorted(dangling)}"
        )

    total = sum(
        len(items)
        for items in CAREER_COMPETENCY_PROFILES.values()
    )

    print("\nCAREERFORGE RESOURCE COMPLETION")
    print("=" * 65)
    print(f"Career profiles: {len(CAREER_COMPETENCY_PROFILES)}")
    print(f"Total competencies: {total}")
    print(f"Previously missing: {len(before)}")
    print(f"New resource definitions: {len(new_definitions)}")
    print(f"New or repaired mappings: {len(new_mappings)}")
    print(f"Remaining gaps: {len(after)}")
    print(f"Expected coverage: {total - len(after)}/{total}")

    print("\nASSIGNMENTS")
    for career, key, urls in new_mappings:
        print(f"  {career}/{key}: {len(urls)} resource(s)")

    print("\nRESOURCE DEFINITIONS")
    for title in new_definitions:
        print(f"  + {title}")

    if not apply:
        print("\nDRY RUN: catalog unchanged.")
        return

    if not new_definitions and not new_mappings:
        print("\nNothing to update.")
        return

    CATALOG_PATH.write_text(
        json.dumps(
            catalog,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    print("\nCatalog successfully updated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply validated resource assignments.",
    )

    args = parser.parse_args()

    complete_catalog(apply=args.apply)