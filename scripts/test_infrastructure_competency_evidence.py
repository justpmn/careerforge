
from src.preprocessing.competency_evidence_extractor import (
    extract_competency_evidence,
)


TEST_CASES = {
    "cloud_engineer": {
        "text": (
            "Managed cloud infrastructure and virtual private clouds. "
            "Configured IAM policies and Terraform modules. "
            "Performed cloud deployments using Amazon CloudWatch "
            "and configured automated failover."
        ),
        "expected": [
            "cloud_infrastructure",
            "cloud_networking",
            "cloud_iam",
            "infrastructure_as_code",
            "cloud_deployment",
            "cloud_monitoring",
            "cloud_reliability",
        ],
    },

    "devops_sre": {
        "text": (
            "Implemented infrastructure as code and automated "
            "deployment pipelines. Wrote Ansible playbooks, "
            "configured distributed tracing, conducted incident "
            "postmortems and defined service-level objectives."
        ),
        "expected": [
            "infrastructure_as_code",
            "deployment_automation",
            "configuration_management",
            "observability",
            "incident_management",
            "sre_reliability",
        ],
    },

    "cybersecurity_analyst": {
        "text": (
            "Monitored security logs and performed threat hunting. "
            "Conducted security incident triage, vulnerability "
            "scanning and security hardening. Implemented identity "
            "and access management, packet analysis, security "
            "risk assessment and ISO 27001 compliance."
        ),
        "expected": [
            "security_monitoring",
            "threat_detection",
            "security_incident_response",
            "vulnerability_assessment",
            "security_controls",
            "identity_access_security",
            "network_security",
            "security_risk",
            "security_compliance",
        ],
    },

    "systems_network_admin": {
        "text": (
            "Performed server administration and configured routers. "
            "Handled network troubleshooting and Active Directory "
            "administration. Monitored system health, managed "
            "system backups, server patching and "
            "user access provisioning."
        ),
        "expected": [
            "systems_administration",
            "network_configuration",
            "network_troubleshooting",
            "directory_management",
            "system_monitoring",
            "system_backup_recovery",
            "patch_management",
            "access_permissions",
        ],
    },

    "it_support": {
        "text": (
            "Provided IT support and troubleshooting. "
            "Handled printer installation, software installation, "
            "Wi-Fi troubleshooting and password resets. "
            "Resolved support tickets, walked users through "
            "fixes and wrote knowledge base articles."
        ),
        "expected": [
            "debugging",
            "end_user_support",
            "hardware_support",
            "software_support",
            "connectivity_support",
            "account_support",
            "ticket_management",
            "customer_communication",
            "knowledge_documentation",
        ],
    },
}


def main():
    total_checks = 0

    for career, case in TEST_CASES.items():
        print(f"\n{'=' * 55}")
        print(f"CAREER: {career}")
        print("=" * 55)

        result = extract_competency_evidence(case["text"])

        for competency in case["expected"]:
            matches = result.get(competency, [])

            assert matches, (
                f"{career}: Missing evidence for {competency}"
            )

            print(
                f"PASS: {competency} "
                f"-> {matches[0]['matched_phrase']}"
            )
            total_checks += 1

        print(
            f"\n{career}: "
            f"{len(case['expected'])} checks passed"
        )

    print(
        f"\nALL {total_checks} INFRASTRUCTURE "
        f"EVIDENCE CHECKS PASSED"
    )


if __name__ == "__main__":
    main()
