from src.backend.app.services.competency_templates import (get_common_groups)
CAREER_COMPETENCY_PROFILES = {
    "backend_developer": [
        {
            "key": "programming",
            "name": "Backend programming language",
            "level": "core",
            "any_of": [
                "Python",
                "JavaScript",
                "TypeScript",
                "Java",
                "Go",
                "C#",
                "PHP",
            ],
            
            
        },
        {
            "key": "backend_runtime",
            "name": "Backend framework or runtime",
            "level": "core",
            "any_of": [
                "Node.js",
                "Express",
                "FastAPI",
                "Django",
                "Flask",
                "Spring Boot",
                "ASP.NET Core",
            ],
        },
        {
            "key": "database",
            "name": "Database technology",
            "level": "core",
            "any_of": [
                "PostgreSQL",
                "MySQL",
                "Microsoft SQL Server",
                "SQLite",
                "MongoDB",
            ],
        },
        {
            "key": "api",
            "name": "API development",
            "level": "core",
            "any_of": [
                "RESTful API",
                "GraphQL",
            ],
        },
        {
            "key": "version_control",
            "name": "Version control",
            "level": "core",
            "any_of": [
                "Git",
            ],
        },
        {
            "key": "deployment",
            "name": "Deployment and infrastructure",
            "level": "supporting",
            "any_of": [
                "Docker",
                "Amazon Web Services (AWS)",
                "Microsoft Azure",
                "Google Cloud",
            ],
        },
        {
            "key": "testing",
            "name": "Automated testing",
            "level": "core",
            "assessment": "manual_review",
            "any_of": [],
        },
        {
            "key": "authentication_security",
            "name": "Authentication and application security",
            "level": "core",
            "assessment": "manual_review",
            "any_of": [],
        },
        {
            "key": "debugging",
            "name": "Debugging and troubleshooting",
            "level": "core",
            "assessment": "manual_review",
            "any_of": [],
        },
        {
            "key": "ci_cd",
            "name": "Continuous integration and delivery",
            "level": "supporting",
            "assessment": "manual_review",
            "any_of": [],
        },
    ]
}
CAREER_COMPETENCY_PROFILES["frontend_developer"] = [
    {
        "key": "web_programming",
        "name": "Frontend programming language",
        "level": "core",
        "any_of": [
            "JavaScript",
            "TypeScript",
        ],
    },

    {
        "key": "web_fundamentals",
        "name": "Web structure and styling",
        "level": "core",
        "any_of": [
            "HTML/CSS",
        ],
    },

    {
        "key": "frontend_framework",
        "name": "Frontend framework or library",
        "level": "supporting",
        "any_of": [
            "React",
            "Angular",
            "Vue.js",
            "Next.js",
        ],
    },

    {
        "key": "build_tools",
        "name": "Frontend build tooling",
        "level": "supporting",
        "any_of": [
            "Vite",
            "Webpack",
            "npm",
        ],
    },

    {
        "key": "web_accessibility",
        "name": "Web accessibility and responsive design",
        "level": "core",
        "assessment": "manual_review",
        "any_of": [],
    },

    *get_common_groups(
        "version_control",
        "testing",
        "ci_cd",
    ),
]
CAREER_COMPETENCY_PROFILES["data_engineer"] = [
    {
        "key": "data_programming",
        "name": "Data engineering programming language",
        "level": "core",
        "any_of": [
            "Python",
            "Java",
        ],
    },

    {
        "key": "sql_querying",
        "name": "SQL querying",
        "level": "core",
        "any_of": [
            "SQL",
        ],
    },

    {
        "key": "data_storage",
        "name": "Database or analytical storage technology",
        "level": "core",
        "any_of": [
            "PostgreSQL",
            "MySQL",
            "Microsoft SQL Server",
            "BigQuery",
        ],
    },

    {
        "key": "pipeline_design",
        "name": "Data pipeline design and orchestration",
        "level": "core",
        "assessment": "manual_review",
        "any_of": [],
    },

    {
        "key": "data_modeling",
        "name": "Data modeling and transformation",
        "level": "core",
        "assessment": "manual_review",
        "any_of": [],
    },

    {
        "key": "data_quality",
        "name": "Data quality and validation",
        "level": "core",
        "assessment": "manual_review",
        "any_of": [],
    },

    *get_common_groups(
        "version_control",
        "cloud_platform",
        "containers",
        "ci_cd",
    ),
]