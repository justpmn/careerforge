import json
from pathlib import Path

from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "src/frontend/src/lib/skilltrees"


def n(key, title, *requires):
    return key, title, list(requires)


# Prerequisites define a suggested learning order.
# They do not lock nodes or prove that a skill has been mastered.

TREE_SPECS = {
    # =========================================
    # DATA / BUSINESS ANALYST — 11
    # =========================================
    "data_business_analyst": [
        n("spreadsheet_tools", "Spreadsheets"),
        n("sql", "SQL"),
        n("analysis_programming", "Analysis Programming"),
        n("requirements_analysis", "Requirements Analysis"),
        n("analytical_databases", "Analytical Databases", "sql"),
        n("data_quality", "Data Quality", "sql"),
        n(
            "analysis_interpretation", "Data Analysis",
            "spreadsheet_tools", "sql",
        ),
        n("bi_tools", "BI Tools", "spreadsheet_tools"),
        n(
            "business_metrics", "Business Metrics",
            "requirements_analysis", "analysis_interpretation",
        ),
        n(
            "reporting_dashboards", "Dashboards",
            "analysis_interpretation", "bi_tools",
        ),
        n(
            "data_communication", "Communicating Insights",
            "reporting_dashboards", "business_metrics",
        ),
    ],

    # =========================================
    # EMBEDDED DEVELOPER — 9
    # =========================================
    "embedded_developer": [
        n("embedded_languages", "Embedded Programming"),
        n("version_control", "Git"),
        n(
            "embedded_microcontrollers", "Microcontrollers",
            "embedded_languages",
        ),
        n(
            "embedded_build_tools", "Build Tools",
            "embedded_languages",
        ),
        n(
            "embedded_interfaces", "Hardware Interfaces",
            "embedded_microcontrollers",
        ),
        n(
            "embedded_firmware", "Firmware",
            "embedded_microcontrollers", "embedded_build_tools",
        ),
        n(
            "embedded_real_time", "Real-Time Systems",
            "embedded_firmware",
        ),
        n(
            "embedded_debugging", "Hardware Debugging",
            "embedded_firmware", "embedded_interfaces",
        ),
        n(
            "embedded_testing", "Embedded Testing",
            "embedded_debugging", "embedded_real_time",
        ),
    ],

    # =========================================
    # GAME DEVELOPER — 9
    # =========================================
    "game_developer": [
        n("game_languages", "Game Programming"),
        n("version_control", "Git"),
        n("game_design", "Game Design"),
        n("game_engine", "Game Engines", "game_languages"),
        n(
            "gameplay_programming", "Gameplay Systems",
            "game_languages", "game_engine",
        ),
        n("game_rendering", "Graphics and Rendering", "game_engine"),
        n(
            "game_physics", "Physics and Collisions",
            "gameplay_programming",
        ),
        n(
            "game_testing", "Game Testing",
            "game_design", "gameplay_programming",
        ),
        n(
            "game_optimization", "Game Optimization",
            "game_rendering", "game_physics",
        ),
    ],

    # =========================================
    # IT PROJECT MANAGER — 13
    # =========================================
    "it_project_manager": [
        n("delivery_methodologies", "Delivery Methods"),
        n("project_management_tools", "Project Tools"),
        n("project_reporting_tools", "Reporting Tools"),
        n(
            "project_planning", "Project Planning",
            "delivery_methodologies",
        ),
        n(
            "scope_management", "Scope Management",
            "project_planning",
        ),
        n(
            "stakeholder_management", "Stakeholder Management",
            "project_planning",
        ),
        n(
            "project_scheduling", "Scheduling",
            "scope_management", "project_management_tools",
        ),
        n(
            "budget_management", "Project Budgeting",
            "project_scheduling",
        ),
        n(
            "project_risk_management", "Risk Management",
            "project_planning",
        ),
        n(
            "project_communication", "Project Communication",
            "stakeholder_management", "project_reporting_tools",
        ),
        n(
            "project_quality_management", "Quality Management",
            "scope_management",
        ),
        n(
            "project_change_management", "Change Management",
            "scope_management", "project_risk_management",
        ),
        n(
            "project_delivery", "Project Delivery",
            "project_scheduling", "project_risk_management",
            "project_quality_management",
        ),
    ],

    # =========================================
    # IT SUPPORT — 12
    # =========================================
    "it_support": [
        n("os_familiarity", "Operating Systems"),
        n("customer_communication", "User Communication"),
        n("support_ticketing_tooling", "Service Desk Tools"),
        n("directory_tooling", "Directory Tools", "os_familiarity"),
        n("hardware_support", "Hardware Support", "os_familiarity"),
        n("software_support", "Software Support", "os_familiarity"),
        n(
            "connectivity_support", "Network Troubleshooting",
            "os_familiarity",
        ),
        n("account_support", "Account Support", "directory_tooling"),
        n(
            "debugging", "Troubleshooting",
            "hardware_support", "software_support",
            "connectivity_support",
        ),
        n(
            "end_user_support", "End-User Support",
            "debugging", "customer_communication",
        ),
        n(
            "ticket_management", "Ticket Management",
            "support_ticketing_tooling", "end_user_support",
        ),
        n(
            "knowledge_documentation", "Knowledge Articles",
            "ticket_management",
        ),
    ],

    # =========================================
    # PRODUCT MANAGER — 11
    # =========================================
    "product_manager": [
        n("product_management_tools", "Product Tools"),
        n("product_analytics_tools", "Analytics Tools"),
        n("product_discovery", "Product Discovery"),
        n(
            "product_strategy", "Product Strategy",
            "product_discovery",
        ),
        n(
            "requirements_analysis", "Product Requirements",
            "product_discovery",
        ),
        n(
            "stakeholder_management", "Stakeholder Alignment",
            "product_strategy",
        ),
        n(
            "product_roadmap", "Product Roadmap",
            "product_strategy", "requirements_analysis",
        ),
        n(
            "feature_prioritization", "Prioritization",
            "product_roadmap",
        ),
        n(
            "product_metrics", "Product Metrics",
            "product_analytics_tools", "product_strategy",
        ),
        n(
            "product_experimentation", "Experimentation",
            "feature_prioritization", "product_metrics",
        ),
        n(
            "product_launch", "Product Launch",
            "feature_prioritization", "stakeholder_management",
        ),
    ],

    # =========================================
    # SOFTWARE ARCHITECT — 10
    # =========================================
    "software_architect": [
        n("programming", "Programming"),
        n("version_control", "Git"),
        n("cloud_platform", "Cloud Platforms"),
        n("containers", "Containers"),
        n("software_design", "Software Design", "programming"),
        n(
            "database_architecture", "Database Architecture",
            "software_design",
        ),
        n(
            "system_design", "System Design",
            "software_design", "database_architecture",
        ),
        n(
            "security_architecture", "Security Architecture",
            "system_design",
        ),
        n(
            "scalability_reliability", "Scalability and Reliability",
            "system_design", "cloud_platform",
        ),
        n(
            "technical_leadership", "Technical Leadership",
            "system_design",
        ),
    ],

    # =========================================
    # SYSTEMS / NETWORK ADMIN — 13
    # =========================================
    "systems_network_admin": [
        n("os_platforms", "Server Operating Systems"),
        n("sys_scripting", "Admin Scripting", "os_platforms"),
        n("directory_tooling", "Directory Tools", "os_platforms"),
        n("cloud_platform", "Cloud Platforms"),
        n(
            "systems_administration", "Systems Administration",
            "os_platforms",
        ),
        n(
            "network_configuration", "Network Configuration",
            "os_platforms",
        ),
        n(
            "directory_management", "Directory Management",
            "directory_tooling", "systems_administration",
        ),
        n(
            "network_troubleshooting", "Network Diagnostics",
            "network_configuration",
        ),
        n(
            "firewall_tooling", "Firewall Tools",
            "network_configuration",
        ),
        n(
            "access_permissions", "Access Permissions",
            "directory_management",
        ),
        n(
            "patch_management", "Patch Management",
            "systems_administration",
        ),
        n(
            "system_monitoring", "System Monitoring",
            "systems_administration", "network_troubleshooting",
        ),
        n(
            "system_backup_recovery", "Backup and Recovery",
            "systems_administration",
        ),
    ],

    # =========================================
    # UI / UX DESIGNER — 13
    # =========================================
    "ui_ux_designer": [
        n("user_research", "User Research"),
        n("design_tooling", "Design Tools"),
        n("graphics_tooling", "Graphics Tools"),
        n("frontend_fundamentals", "Frontend Basics"),
        n(
            "information_architecture", "Information Architecture",
            "user_research",
        ),
        n(
            "wireframing", "Wireframing",
            "information_architecture",
        ),
        n("visual_design", "Visual Design", "graphics_tooling"),
        n(
            "interaction_design", "Interaction Design",
            "wireframing",
        ),
        n(
            "prototyping", "Prototyping",
            "wireframing", "design_tooling",
        ),
        n(
            "ux_accessibility", "Accessibility",
            "interaction_design",
        ),
        n(
            "usability_testing", "Usability Testing",
            "prototyping", "user_research",
        ),
        n(
            "design_systems", "Design Systems",
            "visual_design", "interaction_design",
        ),
        n(
            "design_handoff", "Developer Handoff",
            "design_systems", "prototyping",
            "frontend_fundamentals",
        ),
    ],
}


def validate_tree(career_key, spec):
    profile = CAREER_COMPETENCY_PROFILES[career_key]

    expected = {group["key"] for group in profile}
    actual = [key for key, _, _ in spec]

    if len(actual) != len(set(actual)):
        raise ValueError(f"Duplicate nodes: {career_key}")

    missing = expected - set(actual)
    unknown = set(actual) - expected

    if missing or unknown:
        raise ValueError(
            f"{career_key}: "
            f"missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}"
        )

    dependencies = {
        key: requires
        for key, _, requires in spec
    }

    visited = set()
    visiting = set()

    def visit(key):
        if key in visiting:
            raise ValueError(
                f"Circular dependency: {career_key}/{key}"
            )

        if key in visited:
            return

        visiting.add(key)

        for dependency in dependencies[key]:
            if dependency not in dependencies:
                raise ValueError(
                    f"Unknown dependency: "
                    f"{career_key}/{key} -> {dependency}"
                )
            visit(dependency)

        visiting.remove(key)
        visited.add(key)

    for key in dependencies:
        visit(key)


def build_template(career_key, spec):
    profile_by_key = {
        group["key"]: group
        for group in CAREER_COMPETENCY_PROFILES[career_key]
    }

    nodes = []

    for key, title, requires in spec:
        node = {
            "id": key,
            "title": title,
            "requires": requires,
        }

        alternatives = profile_by_key[key].get("any_of") or []

        aliases = sorted({
            alias.strip()
            for alias in alternatives
            if isinstance(alias, str) and alias.strip()
        })

        if aliases:
            node["skillAliases"] = aliases

        nodes.append(node)

    return {
        "version": 1,
        "nodes": nodes,
    }


def main():
    if len(TREE_SPECS) != 9:
        raise ValueError("Expected exactly nine careers")

    # Validate every tree before writing files.
    templates = {}

    for career_key, spec in TREE_SPECS.items():
        validate_tree(career_key, spec)
        templates[career_key] = build_template(career_key, spec)

    total = sum(
        len(template["nodes"])
        for template in templates.values()
    )

    if total != 101:
        raise ValueError(
            f"Expected 101 competencies, found {total}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for career_key, template in templates.items():
        output = OUTPUT_DIR / f"{career_key}.json"

        output.write_text(
            json.dumps(
                template,
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

        print(
            f"CREATED: {output.name} "
            f"({len(template['nodes'])} nodes)"
        )

    print("\nFINAL BATCH COMPLETE")
    print(f"Career trees generated: {len(templates)}")
    print(f"Competency nodes: {total}")


if __name__ == "__main__":
    main()
