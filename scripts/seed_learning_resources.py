
from sqlalchemy import select

from src.backend.app.database.session import SessionLocal
from src.backend.app.database.models.skill import Skill
from src.backend.app.database.models.learning_resource import (
    LearningResource,
)
from src.backend.app.database.models.learning_resource_skill import (
    LearningResourceSkill,
)


RESOURCES = [
    {
        "title": "Build and Share a Containerized Application",
        "provider": "Docker",
        "resource_type": "tutorial",
        "url": (
            "https://docs.docker.com/get-started/"
            "introduction/index.html"
        ),
        "description": (
            "Learn Docker fundamentals by running containers, "
            "building images, and using Docker Compose."
        ),
        "skills": ["Docker"],
    },
    {
        "title": "AWS Cloud Practitioner Training",
        "provider": "Amazon Web Services",
        "resource_type": "learning_path",
        "url": (
            "https://aws.amazon.com/training/"
            "learn-about/cloud-practitioner/"
        ),
        "description": (
            "Foundational AWS learning covering cloud services, "
            "security, pricing, and cloud architecture."
        ),
        "skills": ["Amazon Web Services (AWS)"],
    },
    {
        "title": "Learn Kubernetes Basics",
        "provider": "Kubernetes",
        "resource_type": "tutorial",
        "url": (
            "https://kubernetes.io/docs/tutorials/"
            "kubernetes-basics/"
        ),
        "description": (
            "Introduction to deploying, scaling, updating, "
            "and troubleshooting applications with Kubernetes."
        ),
        "skills": ["Kubernetes"],
    },
    
    {
        "title": "The Python Tutorial",
        "provider": "Python",
        "resource_type": "tutorial",
        "url": "https://docs.python.org/3/tutorial/",
        "description": (
            "Official Python tutorial covering syntax, "
            "data structures, functions, modules, "
            "and object-oriented programming."
        ),
        "skills": ["Python"],
    },
    {
        "title": "JavaScript Guide",
        "provider": "MDN Web Docs",
        "resource_type": "documentation",
        "url": (
            "https://developer.mozilla.org/en-US/"
            "docs/Web/JavaScript/Guide"
        ),
        "description": (
            "Comprehensive JavaScript guide covering "
            "language fundamentals, functions, objects, "
            "asynchronous programming, and modules."
        ),
        "skills": ["JavaScript"],
    },
    {
        "title": "Getting Started with MySQL",
        "provider": "Oracle",
        "resource_type": "tutorial",
        "url": (
            "https://dev.mysql.com/doc/"
            "mysql-getting-started/en/"
        ),
        "description": (
            "Introduction to installing MySQL, "
            "connecting to the server, and "
            "performing basic database operations."
        ),
        "skills": ["MySQL"],
    },
    {
        "title": "Learn React",
        "provider": "React",
        "resource_type": "tutorial",
        "url": "https://react.dev/learn",
        "description": (
            "Official React learning materials covering "
            "components, JSX, props, state, and "
            "interactive user interfaces."
        ),
        "skills": ["React"],
    },
    {
        "title": "Pro Git",
        "provider": "Git",
        "resource_type": "book",
        "url": "https://git-scm.com/book/en/v2",
        "description": (
            "Free Git book covering version control, "
            "branching, merging, remote repositories, "
            "and collaborative development."
        ),
        "skills": ["Git"],
    },
    
    {
        "title": "Learn Java",
        "provider": "Dev.java",
        "resource_type": "tutorial",
        "url": "https://dev.java/learn/",
        "description": (
            "Official Java learning materials covering syntax, "
            "object-oriented programming, collections, and APIs."
        ),
        "skills": ["Java"],
    },
    {
        "title": "The TypeScript Handbook",
        "provider": "TypeScript",
        "resource_type": "documentation",
        "url": "https://www.typescriptlang.org/docs/handbook/intro",
        "description": (
            "Learn TypeScript fundamentals including types, "
            "interfaces, functions, classes, and modules."
        ),
        "skills": ["TypeScript"],
    },
    {
        "title": "Transact-SQL Tutorial",
        "provider": "Microsoft Learn",
        "resource_type": "tutorial",
        "url": (
            "https://learn.microsoft.com/en-us/sql/t-sql/"
            "tutorial-writing-transact-sql-statements"
        ),
        "description": (
            "Introduction to Transact-SQL, database objects, "
            "queries, and permissions in SQL Server."
        ),
        "skills": ["Microsoft SQL Server"],
    },
    {
        "title": "PostgreSQL Tutorial",
        "provider": "PostgreSQL",
        "resource_type": "tutorial",
        "url": "https://www.postgresql.org/docs/current/tutorial.html",
        "description": (
            "Learn PostgreSQL fundamentals, relational databases, "
            "SQL queries, joins, transactions, and views."
        ),
        "skills": ["PostgreSQL"],
    },
    {
        "title": "Getting Started with Go",
        "provider": "Go",
        "resource_type": "tutorial",
        "url": "https://go.dev/doc/tutorial/getting-started",
        "description": (
            "Learn to install Go, write programs, "
            "use modules, and work with packages."
        ),
        "skills": ["Go"],
    },
    {
        "title": "Get Started with C#",
        "provider": "Microsoft Learn",
        "resource_type": "tutorial",
        "url": "https://learn.microsoft.com/en-us/dotnet/csharp/getting-started/",
        "description": (
            "Introduction to C# programming, language "
            "fundamentals, and application development."
        ),
        "skills": ["C#"],
    },
    {
        "title": "PHP Getting Started",
        "provider": "PHP",
        "resource_type": "tutorial",
        "url": "https://www.php.net/manual/en/getting-started.php",
        "description": (
            "Introduction to PHP programming, "
            "dynamic webpages, and form handling."
        ),
        "skills": ["PHP"],
    },
    {
        "title": "REST Architecture Overview",
        "provider": "MDN Web Docs",
        "resource_type": "documentation",
        "url": "https://developer.mozilla.org/en-US/docs/Glossary/REST",
        "description": (
            "Overview of REST architecture and the "
            "principles behind RESTful web services."
        ),
        "skills": ["RESTful API"],
    },
    {
        "title": "SQLBolt Interactive SQL Lessons",
        "provider": "SQLBolt",
        "resource_type": "tutorial",
        "url": "https://sqlbolt.com/",
        "description": (
            "Interactive SQL exercises covering queries, "
            "filtering, joins, aggregation, and data modification."
        ),
        "skills": ["SQL"],
    },
    {
        "title": "GraphQL Queries",
        "provider": "GraphQL",
        "resource_type": "documentation",
        "url": "https://graphql.org/learn/queries/",
        "description": (
            "Learn how to query GraphQL APIs, select fields, "
            "and use query operations."
        ),
        "skills": ["GraphQL"],
    },
    {
        "title": "SQLite Quickstart",
        "provider": "SQLite",
        "resource_type": "tutorial",
        "url": "https://www.sqlite.org/quickstart.html",
        "description": (
            "Introduction to SQLite database creation "
            "and basic SQL operations using the command line."
        ),
        "skills": ["SQLite"],
    },
    {
        "title": "FastAPI Tutorial",
        "provider": "FastAPI",
        "resource_type": "tutorial",
        "url": "https://fastapi.tiangolo.com/tutorial/",
        "description": (
            "Official step-by-step guide to building "
            "Python APIs using FastAPI."
        ),
        "skills": ["FastAPI"],
    },
    
    {
        "title": "Flask Tutorial",
        "provider": "Pallets Projects",
        "resource_type": "tutorial",
        "url": "https://flask.palletsprojects.com/en/stable/tutorial/",
        "description": "Build a Python web application using Flask.",
        "skills": ["Flask"],
    },
    {
        "title": "Writing Your First Django App",
        "provider": "Django",
        "resource_type": "tutorial",
        "url": "https://docs.djangoproject.com/en/5.2/intro/tutorial01/",
        "description": "Build a Django application with views and routing.",
        "skills": ["Django"],
    },
    {
        "title": "Express Hello World",
        "provider": "Express",
        "resource_type": "tutorial",
        "url": "https://expressjs.com/en/starter/hello-world/",
        "description": "Create a basic Express web server.",
        "skills": ["Express"],
    },
    {
        "title": "Introduction to Node.js",
        "provider": "Node.js",
        "resource_type": "documentation",
        "url": "https://nodejs.org/learn/getting-started/introduction-to-nodejs",
        "description": "Understand the Node.js runtime and asynchronous I/O.",
        "skills": ["Node.js"],
    },
    {
        "title": "Building a RESTful Web Service with Spring",
        "provider": "Spring",
        "resource_type": "tutorial",
        "url": "https://spring.io/guides/gs/rest-service/",
        "description": "Build a RESTful service using Java and Spring.",
        "skills": ["Spring Boot"],
    },
    {
        "title": "Your First Website",
        "provider": "MDN Web Docs",
        "resource_type": "tutorial",
        "url": (
            "https://developer.mozilla.org/en-US/docs/"
            "Learn_web_development/Getting_started/Your_first_website"
        ),
        "description": "Create and style a webpage using HTML and CSS.",
        "skills": ["HTML/CSS"],
    },
    {
        "title": "Getting Started with MongoDB",
        "provider": "MongoDB",
        "resource_type": "tutorial",
        "url": "https://www.mongodb.com/docs/manual/tutorial/getting-started/",
        "description": "Explore document databases and basic CRUD operations.",
        "skills": ["MongoDB"],
    },
    {
        "title": "An Introduction to R",
        "provider": "R Core Team",
        "resource_type": "documentation",
        "url": "https://stat.ethz.ch/CRAN/doc/manuals/r-release/R-intro.html",
        "description": "Learn R programming, data manipulation and statistics.",
        "skills": ["R"],
    },
    {
        "title": "Get Started with Google Cloud",
        "provider": "Google Cloud",
        "resource_type": "documentation",
        "url": "https://docs.cloud.google.com/docs/get-started/",
        "description": "Explore Google Cloud setup, services and tools.",
        "skills": ["Google Cloud"],
    },
    {
        "title": "Azure Architecture and Services",
        "provider": "Microsoft Learn",
        "resource_type": "learning_path",
        "url": (
            "https://learn.microsoft.com/en-us/training/paths/"
            "azure-fundamentals-describe-azure-architecture-services/"
        ),
        "description": "Learn Azure compute, networking, storage and security.",
        "skills": ["Microsoft Azure"],
    },
    {
        "title": "Create a Web API with ASP.NET Core",
        "provider": "Microsoft Learn",
        "resource_type": "tutorial",
        "url": (
            "https://learn.microsoft.com/en-us/aspnet/core/"
            "tutorials/first-web-api?view=aspnetcore-10.0"
        ),
        "description": "Build a RESTful web API using ASP.NET Core.",
        "skills": ["ASP.NET Core"],
    },
    {
        "title": "GNU Bash Manual",
        "provider": "GNU Project",
        "resource_type": "documentation",
        "url": "https://www.gnu.org/software/bash/manual/",
        "description": "Learn Bash commands, variables and shell scripting.",
        "skills": ["Bash/Shell (all shells)"],
    },
    {
        "title": "Getting Started with PowerShell",
        "provider": "Microsoft Learn",
        "resource_type": "tutorial",
        "url": (
            "https://learn.microsoft.com/en-us/powershell/"
            "scripting/learn/ps101/01-getting-started"
        ),
        "description": "Learn PowerShell commands and scripting fundamentals.",
        "skills": ["PowerShell"],
    },

    {
        "title": "BigQuery Documentation and Quickstarts",
        "provider": "Google Cloud",
        "resource_type": "documentation",
        "url": "https://docs.cloud.google.com/bigquery/docs/",
        "description": "Learn cloud data warehousing and analytics with BigQuery.",
        "skills": ["BigQuery"],
    },
    {
        "title": "Getting Started with Looker",
        "provider": "Google Cloud",
        "resource_type": "documentation",
        "url": "https://docs.cloud.google.com/looker/docs/intro",
        "description": "Explore business intelligence, dashboards and data visualization.",
        "skills": ["Google Looker Analytics"],
    },
    {
        "title": "Get Started with Power BI Desktop",
        "provider": "Microsoft Learn",
        "resource_type": "tutorial",
        "url": "https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started",
        "description": "Connect, transform and visualize data using Power BI.",
        "skills": ["Microsoft Power BI"],
    },
    {
        "title": "Build a Basic View in Tableau",
        "provider": "Tableau",
        "resource_type": "tutorial",
        "url": "https://help.tableau.com/current/pro/desktop/en-us/getstarted_buildmanual_ex1basic.htm",
        "description": "Learn to explore data and create basic Tableau visualizations.",
        "skills": ["Tableau"],
    },
    {
        "title": "Snowflake Getting Started",
        "provider": "Snowflake",
        "resource_type": "documentation",
        "url": "https://docs.snowflake.com/en/user-guide-getting-started",
        "description": "Explore Snowflake architecture, queries and data loading.",
        "skills": ["Snowflake"],
    },
    {
        "title": "Learn the Basics of PyTorch",
        "provider": "PyTorch",
        "resource_type": "tutorial",
        "url": "https://docs.pytorch.org/tutorials/beginner/basics/intro.html",
        "description": "Build and train neural networks using PyTorch.",
        "skills": ["PyTorch"],
    },
    {
        "title": "Scikit-learn Getting Started",
        "provider": "Scikit-learn",
        "resource_type": "tutorial",
        "url": "https://scikit-learn.org/stable/getting_started",
        "description": "Learn machine learning estimators, pipelines and evaluation.",
        "skills": ["Scikit-learn"],
    },
    {
        "title": "TensorFlow Quickstart for Beginners",
        "provider": "TensorFlow",
        "resource_type": "tutorial",
        "url": "https://www.tensorflow.org/tutorials/quickstart/beginner.html",
        "description": "Train and evaluate a neural network using TensorFlow.",
        "skills": ["TensorFlow"],
    },
    {
        "title": "NumPy: Absolute Basics for Beginners",
        "provider": "NumPy",
        "resource_type": "tutorial",
        "url": "https://numpy.org/doc/stable/user/absolute_beginners",
        "description": "Learn numerical arrays and fundamental NumPy operations.",
        "skills": ["NumPy"],
    },
    {
        "title": "Getting Started with pandas",
        "provider": "pandas",
        "resource_type": "tutorial",
        "url": "https://pandas.pydata.org/docs/getting_started/",
        "description": "Learn DataFrames, data manipulation, cleaning and analysis.",
        "skills": ["pandas"],
    },
    {
        "title": "Getting Started with AWS CloudFormation",
        "provider": "Amazon Web Services",
        "resource_type": "tutorial",
        "url": "https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/GettingStarted.html",
        "description": "Learn to provision AWS infrastructure using CloudFormation stacks.",
        "skills": ["Amazon Web Services AWS CloudFormation"],
    },
    {
        "title": "Getting Started with Ansible",
        "provider": "Ansible",
        "resource_type": "tutorial",
        "url": "https://docs.ansible.com/projects/ansible/latest/getting_started/index.html",
        "description": "Automate infrastructure management using Ansible playbooks.",
        "skills": ["Ansible"],
    },
    {
        "title": "Terraform AWS Getting Started Tutorials",
        "provider": "HashiCorp",
        "resource_type": "tutorial",
        "url": "https://developer.hashicorp.com/terraform/tutorials/aws-get-started",
        "description": "Manage cloud infrastructure using Terraform configurations.",
        "skills": ["Terraform"],
    },
    {
        "title": "Build a Java Application with Jenkins",
        "provider": "Jenkins",
        "resource_type": "tutorial",
        "url": "https://www.jenkins.io/doc/tutorials/build-a-java-app-with-maven/",
        "description": "Build, test and deliver an application using a Jenkins pipeline.",
        "skills": ["Jenkins CI"],
    },
    {
        "title": "Prometheus Getting Started",
        "provider": "Prometheus",
        "resource_type": "tutorial",
        "url": "https://prometheus.io/docs/prometheus/latest/getting_started/",
        "description": "Learn metrics collection, monitoring and Prometheus queries.",
        "skills": ["Prometheus"],
    },
    {
        "title": "Splunk Search Tutorials",
        "provider": "Splunk",
        "resource_type": "documentation",
        "url": "https://help.splunk.com/en/splunk-enterprise/search",
        "description": "Learn to search and analyze machine data using Splunk.",
        "skills": ["Splunk"],
    },
    {
        "title": "Linux Command Line for Beginners",
        "provider": "Ubuntu",
        "resource_type": "tutorial",
        "url": "https://ubuntu.com/desktop/docs/en/latest/tutorial/the-linux-command-line-for-beginners/",
        "description": "Learn Linux terminal commands and basic system operations.",
        "skills": ["Linux"],
    },
    {
        "title": "Windows Server Overview",
        "provider": "Microsoft Learn",
        "resource_type": "documentation",
        "url": "https://learn.microsoft.com/en-us/windows-server/get-started/overview",
        "description": "Introduction to Windows Server deployment and management.",
        "skills": ["Microsoft Windows Server"],
    },
    {
        "title": "Active Directory Domain Services Overview",
        "provider": "Microsoft Learn",
        "resource_type": "documentation",
        "url": "https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview",
        "description": "Understand Active Directory, authentication and domains.",
        "skills": ["Microsoft Active Directory"],
    },
    {
        "title": "Try Jupyter Online",
        "provider": "Project Jupyter",
        "resource_type": "interactive",
        "url": "https://jupyter.org/try",
        "description": "Explore Jupyter Notebook and JupyterLab interactively.",
        "skills": ["Jupyter Notebook/JupyterLab"],
    },

    {
        "title": "Configure Windows Firewall Rules",
        "provider": "Microsoft Learn",
        "resource_type": "tutorial",
        "url": (
            "https://learn.microsoft.com/en-us/windows/security/"
            "operating-system-security/network-security/"
            "windows-firewall/configure"
        ),
        "description": (
            "Learn practical firewall administration by configuring "
            "inbound and outbound rules in Windows Firewall."
        ),
        "skills": ["Firewall software"],
    },
    {
        "title": "Red Hat Enterprise Linux Documentation",
        "provider": "Red Hat",
        "resource_type": "documentation",
        "url": (
            "https://docs.redhat.com/en/documentation/"
            "red_hat_enterprise_linux/9"
        ),
        "description": (
            "Learn RHEL installation, system administration, "
            "networking, security, and software management."
        ),
        "skills": ["Red Hat Enterprise Linux"],
    },
    {
        "title": "Splunk Enterprise Getting Started",
        "provider": "Splunk",
        "resource_type": "documentation",
        "url": "https://help.splunk.com/en/splunk-enterprise/get-started",
        "description": (
            "Learn Splunk Enterprise setup, data ingestion, "
            "searching, reporting, and visualization."
        ),
        "skills": ["Splunk Enterprise"],
    },
    {
        "title": "Get Started with Grafana Cloud",
        "provider": "Grafana Labs",
        "resource_type": "tutorial",
        "url": (
            "https://grafana.com/docs/grafana-cloud/"
            "learn-and-build/get-started/"
        ),
        "description": (
            "Introduction to observability, metrics, logs, "
            "dashboards, and monitoring with Grafana Cloud."
        ),
        "skills": ["Grafana Labs Grafana Cloud"],
    },
    {
        "title": "Azure DevOps Documentation",
        "provider": "Microsoft Learn",
        "resource_type": "documentation",
        "url": "https://learn.microsoft.com/en-us/azure/devops/",
        "description": (
            "Learn Azure Boards, Repos, Pipelines, "
            "testing, and deployment workflows."
        ),
        "skills": ["Microsoft Azure DevOps Services"],
    },
    {
        "title": "Basic Tasks in Excel",
        "provider": "Microsoft Support",
        "resource_type": "tutorial",
        "url": "https://support.microsoft.com/en-us/excel/basic-tasks-in-excel",
        "description": (
            "Learn Excel worksheets, formulas, tables, "
            "sorting, filtering, and basic data analysis."
        ),
        "skills": ["Microsoft Excel"],
    },
    {
        "title": "Create a Basic Table Report with SSRS",
        "provider": "Microsoft Learn",
        "resource_type": "tutorial",
        "url": (
            "https://learn.microsoft.com/en-us/sql/"
            "reporting-services/"
            "tutorial-creating-a-basic-table-report-report-builder"
        ),
        "description": (
            "Build paginated reports using SQL Server "
            "Reporting Services and Report Builder."
        ),
        "skills": [
            "Microsoft SQL Server Reporting Services SSRS"
        ],
    },
    {
        "title": "Windows 11 Basics",
        "provider": "Microsoft Support",
        "resource_type": "tutorial",
        "url": (
            "https://support.microsoft.com/en-us/windows/"
            "meet-windows-11-easily-switch-to-windows-11-"
            "3a2aa0a7-9559-431f-91a0-d9ca0a1eb0a5"
        ),
        "description": (
            "Learn Windows desktop navigation, "
            "file management, and basic operating system usage."
        ),
        "skills": ["Microsoft Windows"],
    },
    {
        "title": "Oracle PL/SQL Language Reference",
        "provider": "Oracle",
        "resource_type": "documentation",
        "url": (
            "https://docs.oracle.com/en/database/oracle/"
            "oracle-database/19/lnpls/"
        ),
        "description": (
            "Learn PL/SQL fundamentals, procedures, "
            "functions, packages, triggers, and exception handling."
        ),
        "skills": ["Oracle PL/SQL"],
    },
    {
        "title": "Transact-SQL SELECT Examples",
        "provider": "Microsoft Learn",
        "resource_type": "documentation",
        "url": (
            "https://learn.microsoft.com/en-us/sql/"
            "t-sql/queries/select-examples-transact-sql"
        ),
        "description": (
            "Explore practical Transact-SQL SELECT queries "
            "and examples for SQL Server."
        ),
        "skills": ["Transact-SQL"],
    },


    {
        "title": "Learn Angular",
        "provider": "Angular",
        "resource_type": "interactive",
        "url": "https://angular.dev/tutorials/learn-angular",
        "description": "Interactive introduction to Angular components, templates and application development.",
        "skills": ["Angular"],
    },
    {
        "title": "Next.js Dashboard Course",
        "provider": "Next.js",
        "resource_type": "tutorial",
        "url": "https://nextjs.org/learn/dashboard-app",
        "description": "Build a full-stack dashboard using Next.js routing, data fetching and forms.",
        "skills": ["Next.js"],
    },
    {
        "title": "Vue Interactive Tutorial",
        "provider": "Vue.js",
        "resource_type": "interactive",
        "url": "https://vuejs.org/tutorial/",
        "description": "Learn Vue components, reactivity, templates and application fundamentals.",
        "skills": ["Vue.js"],
    },
    {
        "title": "MariaDB Quickstart Guides",
        "provider": "MariaDB",
        "resource_type": "tutorial",
        "url": "https://mariadb.com/docs/server/mariadb-quickstart-guides",
        "description": "Introduction to MariaDB installation, SQL queries and database administration.",
        "skills": ["MariaDB"],
    },
    {
        "title": "Learn Oracle SQL",
        "provider": "Oracle",
        "resource_type": "tutorial",
        "url": "https://www.oracle.com/africa/database/technologies/appdev/sql.html",
        "description": "Learn SQL fundamentals and database operations using Oracle Database.",
        "skills": ["Oracle"],
    },
    {
        "title": "Get Started with Jira Cloud",
        "provider": "Atlassian",
        "resource_type": "tutorial",
        "url": "https://support.atlassian.com/jira-software-cloud/docs/get-started-with-jira-software-cloud/",
        "description": "Learn project tracking, issue management, boards and Jira workflows.",
        "skills": ["Atlassian JIRA"],
    },
    {
        "title": "Create and Organize Work in Confluence",
        "provider": "Atlassian",
        "resource_type": "tutorial",
        "url": "https://support.atlassian.com/confluence-cloud/docs/create-and-organize-work-in-confluence-cloud/",
        "description": "Learn to organize documentation, spaces and collaborative project content.",
        "skills": ["Atlassian Confluence"],
    },
    {
        "title": "Learn C++",
        "provider": "LearnCpp",
        "resource_type": "tutorial",
        "url": "https://www.learncpp.com/",
        "description": "Free modern C++ programming course covering language fundamentals and best practices.",
        "skills": ["C++"],
    },
    {
        "title": "The Rust Programming Language",
        "provider": "Rust",
        "resource_type": "book",
        "url": "https://doc.rust-lang.org/stable/book/",
        "description": "Learn Rust syntax, ownership, error handling and systems programming.",
        "skills": ["Rust"],
    },
    {
        "title": "Figma Design for Beginners",
        "provider": "Figma",
        "resource_type": "tutorial",
        "url": "https://help.figma.com/hc/en-us/sections/30880632542743",
        "description": "Learn UI design, components, auto layout and interactive prototypes.",
        "skills": ["Figma"],
    },
    {
        "title": "Meet Android Studio",
        "provider": "Android Developers",
        "resource_type": "documentation",
        "url": "https://developer.android.com/studio/intro",
        "description": "Introduction to Android Studio, development tools, emulators and debugging.",
        "skills": ["Android Studio"],
    },
    {
        "title": "Get Started with Kotlin",
        "provider": "Kotlin",
        "resource_type": "tutorial",
        "url": "https://kotlinlang.org/docs/getting-started.html",
        "description": "Learn Kotlin development for Android, backend and multiplatform applications.",
        "skills": ["Kotlin"],
    },
    {
        "title": "Dart Tutorial",
        "provider": "Dart",
        "resource_type": "tutorial",
        "url": "https://dart.dev/learn/tutorial",
        "description": "Learn Dart syntax, functions, classes, asynchronous programming and testing.",
        "skills": ["Dart"],
    },
    {
        "title": "Firebase Fundamentals",
        "provider": "Google Firebase",
        "resource_type": "documentation",
        "url": "https://firebase.google.com/docs/guides",
        "description": "Learn Firebase project setup, authentication, databases and application integration.",
        "skills": ["Firebase"],
    },
    {
        "title": "Adobe Illustrator Tutorials",
        "provider": "Adobe",
        "resource_type": "tutorial",
        "url": "https://helpx.adobe.com/illustrator/tutorials.html",
        "description": "Learn vector illustration, drawing, shapes and visual design using Illustrator.",
        "skills": ["Adobe Illustrator"],
    },
    {
        "title": "Adobe Photoshop Tutorials",
        "provider": "Adobe",
        "resource_type": "tutorial",
        "url": "https://helpx.adobe.com/photoshop/tutorials.html",
        "description": "Learn image editing, selections, layers and digital design using Photoshop.",
        "skills": ["Adobe Photoshop"],
    },
    {
        "title": "Adobe Learn",
        "provider": "Adobe",
        "resource_type": "learning_path",
        "url": "https://www.adobe.com/learn",
        "description": "Explore tutorials across Adobe Creative Cloud applications and creative workflows.",
        "skills": ["Adobe Creative Cloud software"],
    },

    {
        "title": "Swift Pathway",
        "provider": "Apple Developer",
        "resource_type": "learning_path",
        "url": "https://developer.apple.com/swift/get-started/",
        "description": "Introduction to Swift programming and Apple platform development.",
        "skills": ["Swift"],
    },
    {
        "title": "Create a Project with Xcode",
        "provider": "Apple Developer",
        "resource_type": "tutorial",
        "url": "https://developer.apple.com/tutorials/develop-in-swift/create-a-project",
        "description": "Learn Xcode setup, project creation and development tools.",
        "skills": ["Xcode"],
    },
    {
        "title": "Vite Getting Started",
        "provider": "Vite",
        "resource_type": "tutorial",
        "url": "https://vite.dev/guide/",
        "description": "Set up and build modern web applications using Vite.",
        "skills": ["Vite"],
    },
    {
        "title": "Webpack Getting Started",
        "provider": "Webpack",
        "resource_type": "tutorial",
        "url": "https://webpack.js.org/guides/getting-started/",
        "description": "Learn JavaScript module bundling and build configuration.",
        "skills": ["Webpack"],
    },
    {
        "title": "About npm",
        "provider": "npm",
        "resource_type": "documentation",
        "url": "https://docs.npmjs.com/about-npm/",
        "description": "Introduction to JavaScript package management and npm.",
        "skills": ["npm"],
    },
    {
        "title": "Redis Data Store Quickstart",
        "provider": "Redis",
        "resource_type": "tutorial",
        "url": "https://redis.io/docs/latest/develop/get-started/data-store/",
        "description": "Learn Redis setup, key-value storage and basic commands.",
        "skills": ["Redis"],
    },
    {
        "title": "NoSQL Databases Explained",
        "provider": "MongoDB",
        "resource_type": "documentation",
        "url": "https://www.mongodb.com/resources/basics/databases/nosql-explained",
        "description": "Explore NoSQL database models, concepts and use cases.",
        "skills": ["NoSQL"],
    },
    {
        "title": "C Language Documentation",
        "provider": "Microsoft Learn",
        "resource_type": "documentation",
        "url": "https://learn.microsoft.com/en-us/cpp/c-language/",
        "description": "Learn C programming fundamentals, syntax and language concepts.",
        "skills": ["C"],
    },
    {
        "title": "Microsoft Macro Assembler Reference",
        "provider": "Microsoft Learn",
        "resource_type": "documentation",
        "url": "https://learn.microsoft.com/en-us/cpp/assembler/masm/microsoft-macro-assembler-reference",
        "description": "Reference for x86 and x64 assembly programming using MASM.",
        "skills": ["Assembly"],
    },
    {
        "title": "Programming in Lua",
        "provider": "Lua.org",
        "resource_type": "book",
        "url": "https://www.lua.org/pil/contents.html",
        "description": "Introduction to Lua programming using the freely available first edition.",
        "skills": ["Lua"],
    },
    {
        "title": "GNU Make Manual",
        "provider": "GNU Project",
        "resource_type": "documentation",
        "url": "https://www.gnu.org/software/make/manual/make.html",
        "description": "Learn Makefiles, build automation, targets and dependencies.",
        "skills": ["Make"],
    },
    {
        "title": "Ninja Build System Manual",
        "provider": "Ninja",
        "resource_type": "documentation",
        "url": "https://ninja-build.org/manual.html",
        "description": "Understand Ninja build files and dependency-based builds.",
        "skills": ["Ninja"],
    },
    {
        "title": "Google Analytics 4 Training Guide",
        "provider": "Google",
        "resource_type": "learning_path",
        "url": "https://support.google.com/analytics/answer/11828307?hl=en",
        "description": "Access Google Analytics 4 introductory training and learning materials.",
        "skills": ["Google Analytics"],
    },
    {
        "title": "Google Sheets Training",
        "provider": "Google Workspace",
        "resource_type": "tutorial",
        "url": "https://support.google.com/a/users/answer/9282959?hl=en",
        "description": "Learn spreadsheets, formulas, data organization and collaboration.",
        "skills": ["Google Sheets"],
    },
    {
        "title": "ServiceNow Developer Learning",
        "provider": "ServiceNow",
        "resource_type": "learning_path",
        "url": "https://developer.servicenow.com/dev.do",
        "description": "Explore ServiceNow platform development and workflow automation.",
        "skills": ["ServiceNow"],
    },
    {
        "title": "Basic Tasks in Microsoft Project",
        "provider": "Microsoft Support",
        "resource_type": "tutorial",
        "url": "https://support.microsoft.com/en-us/project/basic-tasks-in-project-2",
        "description": "Learn project scheduling, task creation and dependency management.",
        "skills": ["Microsoft Project"],
    },
    {
        "title": "Beginner Tutorial for Visio",
        "provider": "Microsoft Support",
        "resource_type": "tutorial",
        "url": "https://support.microsoft.com/en-us/visio/beginner-tutorial-for-visio",
        "description": "Create flowcharts, network diagrams and other visual models.",
        "skills": ["Microsoft Visio"],
    },
    {
        "title": "Adobe XD Help and Tutorials",
        "provider": "Adobe",
        "resource_type": "documentation",
        "url": "https://helpx.adobe.com/xd/desktop.html",
        "description": "Legacy Adobe XD interface design and prototyping documentation; product in maintenance mode.",
        "skills": ["Adobe XD"],
    },


]


def seed_learning_resources(db):
    # Resolve canonical skill names before inserting anything.
    skills = {
        skill.name: skill
        for skill in db.scalars(select(Skill)).all()
    }

    required_skills = {
        name
        for resource in RESOURCES
        for name in resource["skills"]
    }

    missing = required_skills - skills.keys()

    if missing:
        raise ValueError(
            f"Canonical skills not found: {sorted(missing)}"
        )

    resources_added = 0
    links_added = 0

    for data in RESOURCES:
        # URLs identify curated resources for repeatable imports.
        resource = db.scalar(
            select(LearningResource).where(
                LearningResource.url == data["url"]
            )
        )

        if resource is None:
            resource = LearningResource(
                title=data["title"],
                provider=data["provider"],
                resource_type=data["resource_type"],
                url=data["url"],
                description=data["description"],
            )

            db.add(resource)
            db.flush()
            resources_added += 1

        for skill_name in data["skills"]:
            skill = skills[skill_name]

            existing_link = db.get(
                LearningResourceSkill,
                (resource.id, skill.id),
            )

            if existing_link is not None:
                continue

            db.add(
                LearningResourceSkill(
                    learning_resource_id=resource.id,
                    skill_id=skill.id,
                )
            )

            links_added += 1

    print(f"Resources added: {resources_added}")
    print(f"Skill-resource links added: {links_added}")


def main():
    with SessionLocal() as db:
        try:
            seed_learning_resources(db)
            db.commit()
            print("Learning resources seeded successfully.")

        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    main()
