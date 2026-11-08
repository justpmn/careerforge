
import json
from pathlib import Path

from scripts.complete_json_tree_resources import (
    SOURCES as SHARED_SOURCES,
)
from src.backend.app.services.career_competency_profiles import (
    CAREER_COMPETENCY_PROFILES,
)

ROOT = Path(__file__).resolve().parents[1]
CATALOG = (
    ROOT / "src/backend/app/resource_catalog/competency_resources.json"
)

# Each resource: title, provider, resource type, URL.
# Reuse shared resources from our earlier career batch.
NEW_SOURCES = {
    # Data / Business Analysis
    "excel": (
        "Microsoft Excel Help", "Microsoft", "documentation",
        "https://support.microsoft.com/en-us/excel",
    ),
    "powerbi": (
        "Getting Started with Power BI", "Microsoft Learn",
        "tutorial",
        "https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started",
    ),
    "pandas_stats": (
        "Summary Statistics with pandas", "pandas", "tutorial",
        "https://pandas.pydata.org/docs/getting_started/intro_tutorials/06_calculate_statistics.html",
    ),
    "viz": (
        "From Data to Viz", "From Data to Viz", "tutorial",
        "https://www.data-to-viz.com/",
    ),
    "gx": (
        "Great Expectations Core", "Great Expectations",
        "tutorial",
        "https://docs.greatexpectations.io/docs/core/introduction/try_gx/",
    ),
    "stories": (
        "User Stories", "Atlassian", "documentation",
        "https://www.atlassian.com/agile/project-management/user-stories",
    ),
    "pl300": (
        "Power BI Data Analyst Skills", "Microsoft Learn",
        "documentation",
        "https://learn.microsoft.com/en-us/certifications/resources/study-guides/PL-300",
    ),

    # Embedded Systems
    "arduino": (
        "Arduino Programming and Electronics", "Arduino",
        "tutorial", "https://docs.arduino.cc/learn/",
    ),
    "arduino_debug": (
        "Microcontroller Debugging Fundamentals", "Arduino",
        "tutorial",
        "https://docs.arduino.cc/learn/microcontrollers/debugging/",
    ),
    "platformio": (
        "PlatformIO Documentation", "PlatformIO",
        "documentation", "https://docs.platformio.org/en/latest/",
    ),
    "platformio_test": (
        "PlatformIO Unit Testing", "PlatformIO", "tutorial",
        "https://docs.platformio.org/en/latest/advanced/unit-testing/index.html",
    ),
    "freertos": (
        "FreeRTOS Fundamentals", "Amazon Web Services",
        "documentation",
        "https://docs.aws.amazon.com/freertos/latest/userguide/what-is-freertos.html",
    ),
    "c_lang": (
        "Learn C Programming", "Learn-C.org", "tutorial",
        "https://www.learn-c.org/",
    ),

    # Game Development
    "unity": (
        "Unity Learn", "Unity Technologies", "course",
        "https://learn.unity.com/",
    ),
    "godot": (
        "Your First 2D Game", "Godot", "tutorial",
        "https://docs.godotengine.org/en/stable/getting_started/first_2d_game/index.html",
    ),
    "godot_physics": (
        "Godot Physics Introduction", "Godot",
        "documentation",
        "https://docs.godotengine.org/en/stable/tutorials/physics/physics_introduction.html",
    ),
    "godot_perf": (
        "Godot Performance Optimization", "Godot",
        "documentation",
        "https://docs.godotengine.org/en/stable/tutorials/performance/",
    ),
    "csharp": (
        "Tour of C#", "Microsoft Learn", "tutorial",
        "https://learn.microsoft.com/en-us/dotnet/csharp/tour-of-csharp/",
    ),
    "opengl": (
        "Learn OpenGL", "LearnOpenGL", "tutorial",
        "https://learnopengl.com/Getting-started/OpenGL",
    ),

    # IT Project Management
    "open_pm": (
        "Project Management Open Textbook", "BCcampus",
        "book", "https://opentextbc.ca/projectmanagement/",
    ),
    "pmbok": (
        "PMBOK Guide", "Project Management Institute",
        "documentation", "https://www.pmi.org/standards/pmbok",
    ),
    "scrum": (
        "The Scrum Guide", "Scrum Guides", "documentation",
        "https://scrumguides.org/scrum-guide.html",
    ),
    "jira": (
        "Getting Started with Jira", "Atlassian", "tutorial",
        "https://www.atlassian.com/software/jira/guides/getting-started/basics",
    ),
    "change": (
        "IT Change Management", "Atlassian",
        "documentation",
        "https://www.atlassian.com/itsm/change-management",
    ),
    "knowledge": (
        "Knowledge Management", "Atlassian",
        "documentation",
        "https://www.atlassian.com/itsm/knowledge-management",
    ),

    # IT Support and Systems Administration
    "win_troubleshoot": (
        "Windows Server Troubleshooting", "Microsoft Learn",
        "documentation",
        "https://learn.microsoft.com/en-us/troubleshoot/windows-server/welcome-windows-server",
    ),
    "win_monitor": (
        "Monitor and Troubleshoot Windows Server",
        "Microsoft Learn", "course",
        "https://learn.microsoft.com/en-us/training/paths/monitor-troubleshoot-windows-server-environments/",
    ),
    "google_support": (
        "Google IT Support", "Google / Coursera", "course",
        "https://www.coursera.org/professional-certificates/google-it-support",
    ),
    "ifixit": (
        "PC Repair Guides", "iFixit", "tutorial",
        "https://www.ifixit.com/Device/PC",
    ),
    "ad": (
        "Active Directory Domain Services", "Microsoft Learn",
        "documentation",
        "https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview",
    ),
    "jira_service": (
        "Jira Service Management", "Atlassian",
        "documentation",
        "https://www.atlassian.com/software/jira/service-management",
    ),
    "network": (
        "Computer Networking Fundamentals", "Cloudflare",
        "tutorial",
        "https://www.cloudflare.com/learning/network-layer/what-is-a-computer-network/",
    ),
    "ubuntu": (
        "Ubuntu Server Documentation", "Canonical",
        "documentation", "https://ubuntu.com/server/docs",
    ),
    "server": (
        "Windows Server Documentation", "Microsoft Learn",
        "documentation",
        "https://learn.microsoft.com/en-us/windows-server/",
    ),
    "updates": (
        "Windows Updates and Servicing", "Microsoft Learn",
        "documentation",
        "https://learn.microsoft.com/en-us/windows/deployment/update/",
    ),
    "powershell": (
        "PowerShell Documentation", "Microsoft Learn",
        "documentation",
        "https://learn.microsoft.com/en-us/powershell/scripting/overview",
    ),
    "firewall": (
        "Windows Firewall Overview", "Microsoft Learn",
        "documentation",
        "https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/",
    ),

    # Product Management
    "jpd": (
        "Jira Product Discovery", "Atlassian", "tutorial",
        "https://www.atlassian.com/software/jira/product-discovery/guides/getting-started/introduction",
    ),
    "discovery": (
        "Product Discovery", "Atlassian", "documentation",
        "https://www.atlassian.com/agile/product-management/discovery",
    ),
    "roadmap": (
        "Product Roadmap Guide", "Atlassian",
        "documentation",
        "https://www.atlassian.com/agile/product-management/product-roadmaps",
    ),
    "prioritization": (
        "Product Prioritization", "Atlassian",
        "documentation",
        "https://www.atlassian.com/software/jira/product-discovery/resources/handbook/prioritization",
    ),
    "product_process": (
        "Product Development Process", "Atlassian",
        "documentation",
        "https://www.atlassian.com/agile/product-management/new-product-development-process",
    ),
    "product_metrics": (
        "Growth Product Management", "Atlassian",
        "documentation",
        "https://www.atlassian.com/agile/product-management/growth-product-management",
    ),
    "ab": (
        "A/B Testing Fundamentals", "Optimizely",
        "documentation",
        "https://www.optimizely.com/optimization-glossary/ab-testing/",
    ),
    "ga4": (
        "Google Analytics Setup", "Google Analytics",
        "tutorial",
        "https://support.google.com/analytics/answer/9304153",
    ),

    # Software Architecture
    "c4": (
        "C4 Model for Software Architecture", "C4 Model",
        "documentation", "https://c4model.com/",
    ),
    "aws_arch": (
        "AWS Well-Architected Framework", "Amazon Web Services",
        "documentation",
        "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html",
    ),
    "aws_reliability": (
        "AWS Reliability Pillar", "Amazon Web Services",
        "documentation",
        "https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html",
    ),
    "asvs": (
        "Application Security Verification Standard", "OWASP",
        "documentation",
        "https://owasp.org/www-project-application-security-verification-standard/",
    ),
    "adr": (
        "Architecture Decision Records", "ADR Community",
        "documentation", "https://adr.github.io/",
    ),

    # UI / UX Design
    "ux_research": (
        "UX Research Methods", "Nielsen Norman Group",
        "documentation",
        "https://www.nngroup.com/articles/ux-research-cheat-sheet/",
    ),
    "ux_deliverables": (
        "UX Deliverables and User Flows", "Nielsen Norman Group",
        "documentation",
        "https://www.nngroup.com/articles/ux-deliverables-glossary/",
    ),
    "figma": (
        "Figma Help Center", "Figma", "documentation",
        "https://help.figma.com/hc/en-us",
    ),
    "prototype": (
        "Guide to Prototyping in Figma", "Figma",
        "tutorial",
        "https://help.figma.com/hc/en-us/articles/360040314193-Guide-to-prototyping-in-Figma",
    ),
    "usability": (
        "Usability Testing 101", "Nielsen Norman Group",
        "tutorial",
        "https://www.nngroup.com/articles/usability-testing-101/",
    ),
    "material": (
        "Material Design 3", "Google", "documentation",
        "https://m3.material.io/",
    ),
    "wai": (
        "Web Accessibility Tutorials", "W3C",
        "tutorial", "https://www.w3.org/WAI/tutorials/",
    ),
    "visual_design": (
        "UX Design Disciplines", "Nielsen Norman Group",
        "documentation",
        "https://www.nngroup.com/articles/ux-disciplines-glossary/",
    ),
    "blender": (
        "Blender Manual", "Blender Foundation",
        "documentation",
        "https://docs.blender.org/manual/en/latest/",
    ),
    "mdn": (
        "Learn Web Development", "MDN Web Docs", "tutorial",
        "https://developer.mozilla.org/en-US/docs/Learn_web_development/Getting_started",
    ),
    "handoff": (
        "Guide to Dev Mode in Figma", "Figma",
        "documentation",
        "https://help.figma.com/hc/en-us/articles/15023124644247-Guide-to-Dev-Mode-in-Figma",
    ),
}

SOURCES = {**SHARED_SOURCES, **NEW_SOURCES}


# Each line is:
# competency_key=resource_alias,optional_second_alias
#
# All nine career profiles are validated before saving.
RESOURCE_PLANS = {
    "data_business_analyst": """
analysis_interpretation=pandas_stats
requirements_analysis=stories
reporting_dashboards=powerbi
business_metrics=pl300
data_communication=viz
data_quality=gx
sql=sqlbolt
spreadsheet_tools=excel
bi_tools=powerbi
analysis_programming=python
analytical_databases=postgres
""",

    "embedded_developer": """
embedded_firmware=arduino
embedded_microcontrollers=arduino
embedded_interfaces=arduino
embedded_real_time=freertos
embedded_debugging=arduino_debug
embedded_testing=platformio_test
embedded_languages=c_lang
embedded_build_tools=platformio
version_control=git
""",

    "game_developer": """
game_engine=unity
gameplay_programming=godot
game_design=unity
game_physics=godot_physics
game_testing=unity
game_languages=csharp
game_rendering=opengl
game_optimization=godot_perf
version_control=git
""",

    "it_project_manager": """
project_planning=open_pm,pmbok
scope_management=open_pm
project_scheduling=jira,open_pm
budget_management=open_pm
project_risk_management=open_pm
stakeholder_management=open_pm
project_delivery=scrum,open_pm
project_communication=open_pm,knowledge
project_change_management=change
project_quality_management=open_pm
delivery_methodologies=scrum
project_management_tools=jira
project_reporting_tools=jira,knowledge
""",

    "it_support": """
debugging=win_troubleshoot
end_user_support=google_support
hardware_support=ifixit
software_support=win_troubleshoot
connectivity_support=win_monitor,network
account_support=ad
ticket_management=jira_service
customer_communication=google_support
knowledge_documentation=knowledge
os_familiarity=ubuntu,server
support_ticketing_tooling=jira_service
directory_tooling=ad
""",

    "product_manager": """
product_strategy=jpd,roadmap
product_discovery=discovery
product_roadmap=roadmap
feature_prioritization=prioritization
requirements_analysis=stories
stakeholder_management=jpd
product_metrics=product_metrics
product_launch=product_process
product_experimentation=ab
product_management_tools=jpd
product_analytics_tools=ga4
""",

    "software_architect": """
programming=python
software_design=design_patterns
system_design=c4
scalability_reliability=aws_reliability
database_architecture=db_design
security_architecture=asvs
version_control=git
cloud_platform=aws_arch
containers=docker
technical_leadership=adr
""",

    "systems_network_admin": """
systems_administration=ubuntu,server
network_configuration=network
network_troubleshooting=win_monitor
directory_management=ad
system_monitoring=win_monitor
system_backup_recovery=ubuntu
patch_management=updates
access_permissions=ad
os_platforms=ubuntu,server
sys_scripting=powershell
directory_tooling=ad
firewall_tooling=firewall
cloud_platform=aws
""",

    "ui_ux_designer": """
user_research=ux_research
information_architecture=ux_deliverables
wireframing=ux_deliverables,figma
prototyping=prototype
interaction_design=prototype
usability_testing=usability
design_systems=material
ux_accessibility=wai
visual_design=visual_design
design_tooling=figma
graphics_tooling=blender
frontend_fundamentals=mdn
design_handoff=handoff
""",
}


def parse_plan(career_key, text):
    result = {}

    for raw in text.strip().splitlines():
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        key, separator, aliases_text = line.partition("=")

        key = key.strip()
        aliases = [
            alias.strip()
            for alias in aliases_text.split(",")
            if alias.strip()
        ]

        if not separator or not key or not aliases:
            raise ValueError(f"Invalid mapping: {career_key}/{line}")

        if key in result:
            raise ValueError(f"Duplicate competency: {career_key}/{key}")

        for alias in aliases:
            if alias not in SOURCES:
                raise ValueError(f"Unknown resource alias: {alias}")

        result[key] = aliases

    expected = {
        group["key"]
        for group in CAREER_COMPETENCY_PROFILES[career_key]
    }

    actual = set(result)

    if actual != expected:
        raise ValueError(
            f"{career_key}: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )

    return result


def main():
    # Validate every career before changing the catalog.
    plans = {
        career: parse_plan(career, text)
        for career, text in RESOURCE_PLANS.items()
    }

    total = sum(len(plan) for plan in plans.values())

    if len(plans) != 9 or total != 101:
        raise ValueError(
            f"Expected 9 careers and 101 competencies, got "
            f"{len(plans)} careers and {total} competencies"
        )

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    if catalog.get("version") != 1:
        raise ValueError("Unsupported resource catalog version")

    resources = catalog["resources"]
    mappings = catalog["mappings"]

    known_urls = {item["url"] for item in resources}
    resource_count = 0

    # Insert resource definitions only when URL is new.
    for title, provider, resource_type, url in SOURCES.values():
        if url in known_urls:
            continue

        resources.append({
            "title": title,
            "provider": provider,
            "resource_type": resource_type,
            "url": url,
            "description": (
                f"Learning material for {title.lower()} "
                f"provided by {provider}."
            ),
        })

        known_urls.add(url)
        resource_count += 1

    by_key = {
        (item["career_key"], item["competency_key"]): item
        for item in mappings
    }

    mapping_count = 0

    # Merge mappings rather than duplicating them.
    for career, plan in plans.items():
        for competency, aliases in plan.items():
            urls = list(dict.fromkeys(
                SOURCES[alias][3]
                for alias in aliases
            ))

            key = (career, competency)

            if key in by_key:
                current = by_key[key]["urls"]
                by_key[key]["urls"] = list(
                    dict.fromkeys(current + urls)
                )
            else:
                item = {
                    "career_key": career,
                    "competency_key": competency,
                    "urls": urls,
                }

                mappings.append(item)
                by_key[key] = item
                mapping_count += 1

    # Final checks before saving.
    resource_urls = [item["url"] for item in resources]
    mapping_keys = [
        (item["career_key"], item["competency_key"])
        for item in mappings
    ]

    if len(resource_urls) != len(set(resource_urls)):
        raise ValueError("Duplicate resource URLs")

    if len(mapping_keys) != len(set(mapping_keys)):
        raise ValueError("Duplicate competency mappings")

    # All newly mapped URLs must have resource definitions.
    for career, plan in plans.items():
        for competency, aliases in plan.items():
            for alias in aliases:
                url = SOURCES[alias][3]
                if url not in known_urls:
                    raise ValueError(
                        f"Resource missing: {career}/{competency}: {url}"
                    )

    temporary = CATALOG.with_suffix(".json.tmp")

    temporary.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(CATALOG)

    print("\nFINAL CAREER RESOURCE UPDATE")
    print("=" * 45)
    print(f"Careers validated: {len(plans)}")
    print(f"Competencies validated: {total}")
    print(f"New resource definitions: {resource_count}")
    print(f"New competency mappings: {mapping_count}")
    print(f"Total catalog mappings: {len(mappings)}")
    print("Update successful.")


if __name__ == "__main__":
    main()
