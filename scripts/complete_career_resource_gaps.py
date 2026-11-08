
import json
from pathlib import Path

from scripts.seed_learning_resources import RESOURCES
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG = (
    ROOT
    / "src/backend/app/resource_catalog/competency_resources.json"
)


# Already defined by the original resource seeder.
EXISTING = {
    "auth": "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
    "cloudformation": "https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/GettingStarted.html",
    "terraform": "https://developer.hashicorp.com/terraform/tutorials/aws-get-started",
    "ansible": "https://docs.ansible.com/projects/ansible/latest/getting_started/index.html",
    "github_actions": "https://docs.github.com/en/actions/get-started",
}


# Key: title, provider, resource type, URL, description.
NEW = {
    "accessibility": (
        "Accessibility on the Web",
        "MDN Web Docs",
        "tutorial",
        "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility",
        "Learn accessible HTML, interaction patterns and inclusive web design.",
    ),
    "vpc": (
        "Amazon VPC Fundamentals",
        "Amazon Web Services",
        "documentation",
        "https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html",
        "Understand cloud networks, subnets, routing and connectivity.",
    ),
    "iam": (
        "AWS Identity and Access Management",
        "Amazon Web Services",
        "documentation",
        "https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html",
        "Understand identities, roles, permissions and authorization.",
    ),
    "ecs": (
        "Getting Started with Amazon ECS",
        "Amazon Web Services",
        "tutorial",
        "https://docs.aws.amazon.com/AmazonECS/latest/developerguide/getting-started.html",
        "Learn how to deploy containerized applications in AWS.",
    ),
    "cloudwatch": (
        "Introduction to Amazon CloudWatch",
        "Amazon Web Services",
        "documentation",
        "https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html",
        "Monitor cloud resources, applications and operational health.",
    ),
    "reliability": (
        "AWS Reliability Pillar",
        "Amazon Web Services",
        "documentation",
        "https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html",
        "Explore resilient architecture, scaling and failure recovery.",
    ),
    "opentelemetry": (
        "Observability Primer",
        "OpenTelemetry",
        "documentation",
        "https://opentelemetry.io/docs/concepts/observability-primer/",
        "Understand logs, metrics, traces and system observability.",
    ),
    "sre_incidents": (
        "Managing Incidents",
        "Google SRE",
        "book",
        "https://sre.google/sre-book/managing-incidents/",
        "Learn structured operational incident response and coordination.",
    ),
    "slo": (
        "Service Level Objectives",
        "Google SRE",
        "book",
        "https://sre.google/sre-book/service-level-objectives/",
        "Learn service level indicators, objectives and error budgets.",
    ),
    "security_monitoring": (
        "Advanced Hunting in Microsoft Defender",
        "Microsoft Learn",
        "documentation",
        "https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-overview",
        "Explore security events, threat hunting queries and investigations.",
    ),
    "mitre": (
        "Getting Started with MITRE ATT&CK",
        "MITRE",
        "documentation",
        "https://attack.mitre.org/resources/",
        "Learn adversary tactics, techniques and threat investigation concepts.",
    ),
    "incident_response": (
        "NIST Incident Response Recommendations",
        "NIST",
        "documentation",
        "https://csrc.nist.gov/pubs/sp/800/61/r3/final",
        "Study incident preparation, detection, response and recovery.",
    ),
    "security_testing": (
        "OWASP Web Security Testing Guide",
        "OWASP",
        "documentation",
        "https://owasp.org/projects/web-security-testing-guide",
        "Explore structured security testing and vulnerability assessment.",
    ),
    "cis": (
        "CIS Benchmarks",
        "Center for Internet Security",
        "documentation",
        "https://www.cisecurity.org/cis-benchmarks",
        "Learn secure configuration and system hardening practices.",
    ),
    "network_security": (
        "Azure Network Security Best Practices",
        "Microsoft Learn",
        "documentation",
        "https://learn.microsoft.com/en-us/azure/security/fundamentals/network-best-practices",
        "Learn network segmentation, access controls and security monitoring.",
    ),
    "nist_csf": (
        "NIST Cybersecurity Framework 2.0",
        "NIST",
        "documentation",
        "https://www.nist.gov/cyberframework",
        "Understand cybersecurity risk management and security frameworks.",
    ),
}


# Only fill competencies identified as missing by the audit.
ADDITIONS = {
    "frontend_developer": {
        "web_accessibility": ["accessibility"],
    },
    "full_stack_developer": {
        "authentication_security": ["auth"],
    },
    "cloud_engineer": {
        "cloud_infrastructure": ["cloudformation"],
        "cloud_networking": ["vpc"],
        "cloud_iam": ["iam"],
        "infrastructure_as_code": ["terraform"],
        "cloud_deployment": ["ecs"],
        "cloud_monitoring": ["cloudwatch"],
        "cloud_reliability": ["reliability"],
    },
    "devops_sre": {
        "infrastructure_as_code": ["terraform"],
        "deployment_automation": ["github_actions"],
        "configuration_management": ["ansible"],
        "observability": ["opentelemetry"],
        "incident_management": ["sre_incidents"],
        "sre_reliability": ["slo"],
    },
    "cybersecurity_analyst": {
        "security_monitoring": ["security_monitoring"],
        "threat_detection": ["mitre"],
        "security_incident_response": ["incident_response"],
        "vulnerability_assessment": ["security_testing"],
        "security_controls": ["cis"],
        "identity_access_security": ["auth", "iam"],
        "network_security": ["network_security"],
        "security_risk": ["nist_csf"],
        "security_compliance": ["nist_csf", "cis"],
    },
}


def main():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    if catalog.get("version") != 1:
        raise ValueError("Unsupported catalog version.")

    resources = catalog["resources"]
    mappings = catalog["mappings"]

    new_urls = {
        key: details[3]
        for key, details in NEW.items()
    }
    url_lookup = {**EXISTING, **new_urls}

    # Validate keys against the actual backend profiles.
    for career_key, competencies in ADDITIONS.items():
        valid_keys = {
            group["key"]
            for group in CAREER_COMPETENCY_PROFILES[career_key]
        }

        for competency_key, aliases in competencies.items():
            if competency_key not in valid_keys:
                raise ValueError(
                    f"Unknown competency: {career_key}/{competency_key}"
                )

            for alias in aliases:
                if alias not in url_lookup:
                    raise ValueError(f"Unknown resource alias: {alias}")

    # Insert new resource definitions by URL.
    existing_urls = {
        item["url"]
        for item in resources
    }

    resources_added = 0

    for title, provider, resource_type, url, description in NEW.values():
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
        resources_added += 1

    # Index existing mappings and update without duplicates.
    mapping_index = {
        (item["career_key"], item["competency_key"]): item
        for item in mappings
    }

    mappings_added = 0

    for career_key, competencies in ADDITIONS.items():
        for competency_key, aliases in competencies.items():
            urls = [url_lookup[alias] for alias in aliases]
            key = (career_key, competency_key)

            if key in mapping_index:
                current = mapping_index[key]["urls"]
                mapping_index[key]["urls"] = list(
                    dict.fromkeys(current + urls)
                )
            else:
                item = {
                    "career_key": career_key,
                    "competency_key": competency_key,
                    "urls": urls,
                }
                mappings.append(item)
                mapping_index[key] = item
                mappings_added += 1

    # Check for duplicate resource and mapping entries.
    all_urls = [item["url"] for item in resources]

    if len(all_urls) != len(set(all_urls)):
        raise ValueError("Duplicate resource definitions found.")

    all_keys = [
        (item["career_key"], item["competency_key"])
        for item in mappings
    ]

    if len(all_keys) != len(set(all_keys)):
        raise ValueError("Duplicate competency mappings found.")

    # Validate URLs against this catalog and the original seeder.
    available_urls = set(all_urls)
    available_urls.update(item["url"] for item in RESOURCES)

    missing_urls = {
        url
        for item in mappings
        for url in item["urls"]
        if url not in available_urls
    }

    if missing_urls:
        raise ValueError(
            f"Undefined resource URLs: {sorted(missing_urls)}"
        )

    # Write only after every check has passed.
    temporary_path = CATALOG.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(CATALOG)

    print("\nRESOURCE CATALOG UPDATE")
    print("=" * 45)
    print(f"New resources added: {resources_added}")
    print(f"New mappings added: {mappings_added}")
    print(f"Total resources in catalog: {len(resources)}")
    print(f"Total mappings: {len(mappings)}")
    print("Catalog updated successfully.")


if __name__ == "__main__":
    main()
