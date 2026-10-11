import re


COMPETENCY_PATTERNS = {
    "testing": [
        r"\bautomated tests?\b",
        r"\bautomated testing\b",
        r"\bunit tests?\b",
        r"\bunit testing\b",
        r"\bintegration tests?\b",
        r"\bintegration testing\b",
        r"\bend-to-end tests?\b",
        r"\btest automation\b",
        r"\btest cases?\b",
        r"\bpytest\b",
        r"\bjest\b",
        r"\bjunit\b",
        r"\btestng\b",
    ],

    "authentication_security": [
        r"\bauthentication\b",
        r"\bauthorization\b",
        r"\botp\b",
        r"\bone[- ]time passwords?\b",
        r"\boauth(?:\s*2(?:\.0)?)?\b",
        r"\bjwt\b",
        r"\bjson web tokens?\b",
        r"\baccess control\b",
        r"\bpassword hashing\b",
        r"\brole[- ]based access control\b",
    ],

    "debugging": [
        r"\bdebugging\b",
        r"\bdebugged\b",
        r"\btroubleshooting\b",
        r"\btroubleshot\b",
        r"\bbug fixes?\b",
        r"\bresolved technical issues?\b",
        r"\bdiagnosed (?:system|network|software) issues?\b",
    ],

    "ci_cd": [
        r"\bci\s*/\s*cd\b",
        r"\bcontinuous integration\b",
        r"\bcontinuous delivery\b",
        r"\bcontinuous deployment\b",
        r"\bgithub actions\b",
        r"\bgitlab ci\b",
        r"\bjenkins\b",
        r"\bazure pipelines\b",
    ],
        "web_accessibility": [
        r"\bweb accessibility\b",
        r"\baccessible (?:websites?|interfaces?|UI)\b",
        r"\bWCAG\b",
        r"\bresponsive (?:web )?design\b",
        r"\bmobile[- ]first design\b",
    ],

    "pipeline_design": [
        r"\bETL\b",
        r"\bELT\b",
        r"\bdata pipelines?\b",
        r"\bApache Airflow\b",
        r"\bworkflow orchestration\b",
        r"\bdata ingestion\b",
    ],

    "data_modeling": [
        r"\bdata model(?:ing|ling)\b",
        r"\bdimensional model(?:ing|ling)\b",
        r"\bstar schema\b",
        r"\bdatabase schema design\b",
        r"\bdatabase design\b",
    ],

    "data_quality": [
        r"\bdata quality\b",
        r"\bdata validation\b",
        r"\bdata cleansing\b",
        r"\bdata cleaning\b",
        r"\bdata integrity\b",
        r"\bdata profiling\b",
    ],
    "software_design": [
        r"\bsoftware design\b",
        r"\bsoftware architecture\b",
        r"\bdesign patterns?\b",
        r"\bobject[- ]oriented design\b",
        r"\bSOLID principles?\b",
        r"\bclean architecture\b",
        r"\bmodular architecture\b",
    ],
    
    "system_design": [
        r"\bsystem design\b",
        r"\bsystem architecture\b",
        r"\bdistributed systems?\b",
        r"\bmicroservices architecture\b",
        r"\barchitectural design\b",
    ],

    "scalability_reliability": [
        r"\bscalab(?:le|ility)\b",
        r"\bhigh availability\b",
        r"\bfault toleran(?:ce|t)\b",
        r"\bload balancing\b",
        r"\breliability engineering\b",
    ],

    "database_architecture": [
        r"\bdatabase architecture\b",
        r"\bdatabase design\b",
        r"\bdatabase schema design\b",
        r"\bdata architecture\b",
        r"\bdatabase normalization\b",
    ],

    "security_architecture": [
        r"\bsecurity architecture\b",
        r"\bthreat model(?:ing|ling)\b",
        r"\bsecure system design\b",
        r"\bzero trust architecture\b",
        r"\bsecurity by design\b",
    ],

    "technical_leadership": [
        r"\btechnical lead(?:er)?\b",
        r"\barchitecture decisions?\b",
        r"\bmentored developers?\b",
        r"\bled (?:the )?development team\b",
        r"\btechnical leadership\b",
    ],

    "test_strategy": [
        r"\btest plans?\b",
        r"\btest cases?\b",
        r"\btest strateg(?:y|ies)\b",
        r"\btest scenarios?\b",
        r"\bacceptance testing\b",
    ],

    "defect_management": [
        r"\bdefect tracking\b",
        r"\bbug tracking\b",
        r"\bbug reports?\b",
        r"\bdefect triage\b",
        r"\bissue tracking\b",
    ],

    "api_testing": [
        r"\bAPI tests?\b",
        r"\bAPI testing\b",
        r"\bPostman collections?\b",
        r"\bREST API testing\b",
    ],

    "performance_testing": [
        r"\bperformance testing\b",
        r"\bload testing\b",
        r"\bstress testing\b",
        r"\bApache JMeter\b",
        r"\bk6 load tests?\b",
    ],
    
    # Mobile development
    "mobile_app_development": [
        r"\bmobile app(?:lication)? development\b",
        r"\b(?:developed|built|published) (?:an? )?(?:Android|iOS|mobile) app\b",
        r"\bReact Native\b",
        r"\bFlutter\b",
    ],

    "mobile_ui": [
        r"\bmobile UI\b",
        r"\bmobile user interface\b",
        r"\bJetpack Compose\b",
        r"\bSwiftUI\b",
        r"\bmobile navigation\b",
    ],

    "mobile_platform_integration": [
        r"\bAndroid SDK\b",
        r"\biOS SDK\b",
        r"\bmobile platform APIs?\b",
        r"\bAndroid permissions?\b",
        r"\bpush notifications?\b",
    ],

    "mobile_testing": [
        r"\bmobile app testing\b",
        r"\bEspresso testing\b",
        r"\bXCTest\b",
        r"\bAndroid UI tests?\b",
        r"\biOS UI tests?\b",
    ],

    "mobile_release": [
        r"\bGoogle Play Console\b",
        r"\bApp Store Connect\b",
        r"\bTestFlight\b",
        r"\bapp store submission\b",
        r"\bpublished (?:an? )?(?:Android|iOS|mobile) app\b",
    ],

    # Embedded systems
    "embedded_firmware": [
        r"\bfirmware development\b",
        r"\bembedded firmware\b",
        r"\bbootloaders?\b",
        r"\bfirmware updates?\b",
    ],

    "embedded_microcontrollers": [
        r"\bmicrocontrollers?\b",
        r"\bSTM32\b",
        r"\bESP32\b",
        r"\bARM Cortex[- ]M\b",
        r"\bArduino\b",
    ],

    "embedded_interfaces": [
        r"\bI2C\b",
        r"\bSPI\b",
        r"\bUART\b",
        r"\bGPIO\b",
        r"\bCAN bus\b",
        r"\bperipheral drivers?\b",
    ],

    "embedded_real_time": [
        r"\bRTOS\b",
        r"\bFreeRTOS\b",
        r"\breal[- ]time operating systems?\b",
        r"\binterrupt service routines?\b",
    ],

    "embedded_debugging": [
        r"\bJTAG\b",
        r"\bSWD debugging\b",
        r"\blogic analy[sz]er\b",
        r"\bfirmware debugging\b",
    ],

    "embedded_testing": [
        r"\bhardware[- ]in[- ]the[- ]loop\b",
        r"\bHIL testing\b",
        r"\bfirmware tests?\b",
        r"\bembedded system testing\b",
    ],

    # Game development
    "game_engine": [
        r"\bUnity(?: Engine)?\b",
        r"\bUnreal Engine\b",
        r"\bGodot\b",
        r"\bGameMaker\b",
    ],

    "gameplay_programming": [
        r"\bgameplay programming\b",
        r"\bgame mechanics\b",
        r"\bgame logic\b",
        r"\bplayer controller\b",
        r"\bgame AI\b",
    ],

    "game_design": [
        r"\bgame design\b",
        r"\blevel design\b",
        r"\bgame design document\b",
        r"\bgame balancing\b",
    ],

    "game_physics": [
        r"\bgame physics\b",
        r"\bcollision detection\b",
        r"\brigid[- ]body physics\b",
        r"\bphysics engines?\b",
    ],

    "game_testing": [
        r"\bplaytesting\b",
        r"\bgameplay testing\b",
        r"\bgame QA\b",
        r"\bautomated game testing\b",
    ],

    "game_rendering": [
        r"\bshaders?\b",
        r"\bgraphics programming\b",
        r"\brendering pipelines?\b",
        r"\bOpenGL\b",
        r"\bVulkan\b",
    ],

    "game_optimization": [
        r"\bframe[- ]rate optimi[sz]ation\b",
        r"\bgame performance optimi[sz]ation\b",
        r"\bGPU profiling\b",
        r"\brendering optimization\b",
    ],
    
    # Data science and machine learning
    "statistics_inference": [
        r"\bstatistical (?:analysis|inference|testing|modelling|modeling)\b",
        r"\bhypothesis testing\b",
        r"\bconfidence intervals?\b",
        r"\bregression analysis\b",
        r"\bA/B testing\b",
    ],

    "exploratory_analysis": [
        r"\bexploratory data analysis\b",
        r"\bEDA\b",
        r"\bdata exploration\b",
        r"\bdistribution analysis\b",
    ],

    "data_preparation": [
        r"\bdata (?:cleaning|cleansing|preprocessing|wrangling)\b",
        r"\bfeature engineering\b",
        r"\bmissing[- ]value imputation\b",
        r"\bdata transformation\b",
    ],

    "ml_training": [
        r"\bmodel training\b",
        r"\btrained (?:an? )?(?:ML |machine learning |deep learning )?models?\b",
        r"\bhyperparameter tuning\b",
        r"\bGridSearchCV\b",
        r"\bmodel fine[- ]tuning\b",
    ],

    "model_evaluation": [
        r"\bmodel evaluation\b",
        r"\bmodel validation\b",
        r"\bcross[- ]validation\b",
        r"\bconfusion matrix\b",
        r"\bF1[- ]score\b",
        r"\bROC[- ]AUC\b",
    ],

    "data_communication": [
        r"\bdata storytelling\b",
        r"\bpresented (?:analysis|findings|insights)\b",
        r"\bcommunicat(?:ed|ing) (?:the )?(?:findings|insights)\b",
        r"\banalytical reporting\b",
    ],

    # Production ML engineering
    "model_serving": [
        r"\bmodel deployment\b",
        r"\bmodel serving\b",
        r"\bdeployed (?:an? )?(?:ML |machine learning )?models?\b",
        r"\binference (?:API|endpoint|service|server)\b",
        r"\bserved (?:an? )?(?:trained )?models?\b",
    ],

    "model_monitoring": [
        r"\bmodel monitoring\b",
        r"\bmodel drift\b",
        r"\bdata drift\b",
        r"\binference latency\b",
        r"\bproduction model performance\b",
    ],

    "ml_workflows": [
        r"\bMLOps\b",
        r"\bmodel registry\b",
        r"\bexperiment tracking\b",
        r"\bMLflow\b",
        r"\bautomated model retraining\b",
    ],
    
    # Data and business analysis
    "analysis_interpretation": [
        r"\bdata analysis\b",
        r"\banaly[sz]ed (?:the )?data\b",
        r"\btrend analysis\b",
        r"\bvariance analysis\b",
        r"\binterpreted (?:the )?(?:data|results)\b",
    ],

    "requirements_analysis": [
        r"\bbusiness requirements?\b",
        r"\brequirements elicitation\b",
        r"\bstakeholder interviews?\b",
        r"\bprocess mapping\b",
        r"\bbusiness process analysis\b",
        r"\buser stor(?:y|ies)\b",
    ],

    "reporting_dashboards": [
        r"\bdashboard development\b",
        r"\b(?:built|developed|created) (?:an? )?(?:interactive )?dashboards?\b",
        r"\binteractive dashboards?\b",
        r"\bPower BI reports?\b",
        r"\bautomated reporting\b",
    ],

    "business_metrics": [
        r"\bkey performance indicators?\b",
        r"\bKPIs?\b",
        r"\bbusiness metrics?\b",
        r"\boperational metrics?\b",
        r"\bperformance reporting\b",
    ],

    # Database engineering
    "query_optimization": [
        r"\bquery optimi[sz]ation\b",
        r"\bquery tuning\b",
        r"\bSQL performance tuning\b",
        r"\bexecution plans?\b",
        r"\bEXPLAIN ANALYZE\b",
        r"\bindex optimi[sz]ation\b",
    ],

    "database_administration": [
        r"\bdatabase administration\b",
        r"\bdatabase administrator\b",
        r"\bdatabase replication\b",
        r"\bindex maintenance\b",
        r"\bdatabase maintenance\b",
    ],

    "backup_recovery": [
        r"\bdatabase backups?\b",
        r"\bdatabase restores?\b",
        r"\bpoint[- ]in[- ]time recovery\b",
        r"\bdisaster recovery\b",
        r"\bbackup and recovery\b",
    ],

    "database_security": [
        r"\bdatabase access control\b",
        r"\bdatabase encryption\b",
        r"\bdatabase auditing\b",
        r"\brow[- ]level security\b",
        r"\bdatabase permissions?\b",
    ],

    "database_monitoring": [
        r"\bdatabase monitoring\b",
        r"\bslow query logging\b",
        r"\breplication lag\b",
        r"\bdatabase performance monitoring\b",
        r"\bdatabase health checks?\b",
    ],

    "database_migrations": [
        r"\bdatabase migrations?\b",
        r"\bschema migrations?\b",
        r"\bAlembic migrations?\b",
        r"\bFlyway\b",
        r"\bLiquibase\b",
    ],
    
    # Cloud engineering
    "cloud_infrastructure": [
        r"\bcloud infrastructure provisioning\b",
        r"\bprovisioned cloud resources?\b",
        r"\bmanaged cloud infrastructure\b",
        r"\bconfigured (?:cloud )?virtual machines?\b",
        r"\bEC2 instances?\b",
    ],

    "cloud_networking": [
        r"\bcloud networking\b",
        r"\bvirtual private clouds?\b",
        r"\bVPC configurations?\b",
        r"\bsubnet configurations?\b",
        r"\bsecurity group rules?\b",
        r"\bcloud network architecture\b",
    ],

    "cloud_iam": [
        r"\bIAM policies?\b",
        r"\bAWS IAM\b",
        r"\bcloud identity management\b",
        r"\bconfigured IAM roles?\b",
        r"\bcloud access policies?\b",
        r"\bleast[- ]privilege access\b",
    ],

    "infrastructure_as_code": [
        r"\binfrastructure as code\b",
        r"\bIaC implementation\b",
        r"\bTerraform modules?\b",
        r"\bTerraform configurations?\b",
        r"\bCloudFormation templates?\b",
        r"\bautomated infrastructure provisioning\b",
    ],

    "cloud_deployment": [
        r"\bcloud deployments?\b",
        r"\bdeployed applications? to (?:AWS|Azure|Google Cloud|GCP)\b",
        r"\bdeployed services? (?:on|to) (?:AWS|Azure|Google Cloud|GCP)\b",
        r"\bmanaged cloud deployments?\b",
    ],

    "cloud_monitoring": [
        r"\bcloud infrastructure monitoring\b",
        r"\bcloud resource monitoring\b",
        r"\bAmazon CloudWatch\b",
        r"\bAzure Monitor\b",
        r"\bcloud monitoring dashboards?\b",
    ],

    "cloud_reliability": [
        r"\bcloud auto[- ]scaling\b",
        r"\bconfigured auto[- ]scaling\b",
        r"\bhigh availability architecture\b",
        r"\bautomated failover\b",
        r"\bdisaster recovery planning\b",
        r"\bcloud disaster recovery\b",
    ],

    # DevOps and site reliability
    "deployment_automation": [
        r"\bautomated deployment pipelines?\b",
        r"\bdeployment automation\b",
        r"\brelease automation\b",
        r"\bblue[- ]green deployments?\b",
        r"\brolling deployments?\b",
        r"\bcontinuous deployment pipelines?\b",
    ],

    "configuration_management": [
        r"\bconfiguration management\b",
        r"\bAnsible playbooks?\b",
        r"\bautomated server configuration\b",
        r"\binfrastructure configuration automation\b",
    ],

    "observability": [
        r"\bobservability\b",
        r"\bdistributed tracing\b",
        r"\bapplication telemetry\b",
        r"\bmetrics and logs\b",
        r"\blog aggregation\b",
        r"\bservice[- ]level indicators?\b",
    ],

    "incident_management": [
        r"\bincident management\b",
        r"\bon[- ]call rotations?\b",
        r"\bproduction incident response\b",
        r"\bincident postmortems?\b",
        r"\broot cause analysis\b",
        r"\bproduction outages?\b",
    ],

    "sre_reliability": [
        r"\bsite reliability engineering\b",
        r"\bservice[- ]level objectives?\b",
        r"\berror budgets?\b",
        r"\breliability engineering\b",
        r"\bSLO monitoring\b",
        r"\bdisaster recovery testing\b",
    ],
    
    # Cybersecurity analysis
    "security_monitoring": [
        r"\bSIEM monitoring\b",
        r"\bsecurity event monitoring\b",
        r"\bmonitored security (?:alerts|logs|events)\b",
        r"\bsecurity log analysis\b",
    ],

    "threat_detection": [
        r"\bthreat detection\b",
        r"\bthreat hunting\b",
        r"\bdetected suspicious activity\b",
        r"\bindicators? of compromise\b",
    ],

    "security_incident_response": [
        r"\bsecurity incident response\b",
        r"\bsecurity incident investigation\b",
        r"\bsecurity incident triage\b",
        r"\bincident containment\b",
    ],

    "vulnerability_assessment": [
        r"\bvulnerability (?:assessment|scanning|management)\b",
        r"\bpenetration testing\b",
        r"\bCVE analysis\b",
        r"\bvulnerability remediation\b",
    ],

    "security_controls": [
        r"\bfirewall (?:rules|configuration|policies)\b",
        r"\bendpoint detection and response\b",
        r"\bEDR deployment\b",
        r"\bsecurity hardening\b",
    ],

    "identity_access_security": [
        r"\bidentity and access management\b",
        r"\baccess control policies\b",
        r"\bprivileged access management\b",
        r"\bMFA enforcement\b",
    ],

    "network_security": [
        r"\bnetwork security monitoring\b",
        r"\bnetwork intrusion detection\b",
        r"\bIDS/IPS\b",
        r"\bpacket analysis\b",
        r"\bnetwork traffic inspection\b",
    ],

    "security_risk": [
        r"\bsecurity risk assessment\b",
        r"\bsecurity risk analysis\b",
        r"\bthreat model(?:ing|ling)\b",
        r"\bsecurity audit findings\b",
    ],

    "security_compliance": [
        r"\bISO 27001\b",
        r"\bNIST CSF\b",
        r"\bsecurity compliance audits?\b",
        r"\bPCI DSS\b",
    ],
    
    # Systems and network administration
    "systems_administration": [
        r"\bserver administration\b",
        r"\bsystem administration\b",
        r"\badministered (?:Linux|Windows) servers?\b",
        r"\bmanaged (?:Linux|Windows) servers?\b",
    ],

    "network_configuration": [
        r"\bconfigured routers?\b",
        r"\bconfigured switches?\b",
        r"\bVLAN configuration\b",
        r"\bsubnetting\b",
        r"\brouting configuration\b",
    ],

    "network_troubleshooting": [
        r"\bnetwork troubleshooting\b",
        r"\bDNS troubleshooting\b",
        r"\bnetwork connectivity issues?\b",
        r"\bdiagnosed (?:network|connectivity) issues?\b",
    ],

    "directory_management": [
        r"\bActive Directory administration\b",
        r"\bmanaged user accounts\b",
        r"\bgroup policy management\b",
        r"\bLDAP administration\b",
    ],

    "system_monitoring": [
        r"\bmonitored system health\b",
        r"\bsystem health checks?\b",
        r"\bserver monitoring\b",
        r"\bmonitored server performance\b",
    ],

    "system_backup_recovery": [
        r"\bsystem backups?\b",
        r"\bserver backups?\b",
        r"\bsystem restores?\b",
        r"\bserver disaster recovery\b",
    ],

    "patch_management": [
        r"\bpatch management\b",
        r"\bsecurity patch deployment\b",
        r"\bserver patching\b",
        r"\boperating system updates?\b",
    ],

    "access_permissions": [
        r"\bfile permissions management\b",
        r"\buser access provisioning\b",
        r"\brole[- ]based access control\b",
        r"\bpermission audits?\b",
    ],
    
    # IT support
    "end_user_support": [
        r"\bIT support\b",
        r"\bhelp[- ]?desk support\b",
        r"\bprovided technical support to\b",
        r"\bsupported (?:staff|employees|end users)\b",
    ],

    "hardware_support": [
        r"\bhardware troubleshooting\b",
        r"\bprinter (?:installation|troubleshooting|repair)\b",
        r"\bcomputer hardware repair\b",
        r"\bperipheral setup\b",
    ],

    "software_support": [
        r"\bsoftware installation\b",
        r"\bapplication troubleshooting\b",
        r"\bsoftware configuration\b",
        r"\bdesktop support\b",
    ],

    "connectivity_support": [
        r"\bWi[- ]?Fi troubleshooting\b",
        r"\bnetwork connectivity support\b",
        r"\bVPN troubleshooting\b",
        r"\binternet connection issues?\b",
    ],

    "account_support": [
        r"\bpassword resets?\b",
        r"\baccount provisioning\b",
        r"\buser account support\b",
        r"\baccount unlocks?\b",
    ],

    "ticket_management": [
        r"\bhelp[- ]?desk tickets?\b",
        r"\bservice desk tickets?\b",
        r"\bticket triage\b",
        r"\bresolved support tickets?\b",
    ],

    "customer_communication": [
        r"\bexplained technical issues to (?:users|customers|staff)\b",
        r"\buser communication\b",
        r"\bwalked users through\b",
        r"\bcommunicated resolutions?\b",
    ],

    "knowledge_documentation": [
        r"\bknowledge base articles?\b",
        r"\bsupport documentation\b",
        r"\btroubleshooting guides?\b",
        r"\bdocumented solutions?\b",
    ],




}


COMPILED_PATTERNS = {
    key: [
        re.compile(pattern, re.IGNORECASE)
        for pattern in patterns
    ]
    for key, patterns in COMPETENCY_PATTERNS.items()
}


def extract_competency_evidence(
    text: str,
    max_excerpts: int = 3,
) -> dict:
    """
    Locate explicit resume references to competencies.

    Returns matched phrases and supporting excerpts.
    Does not determine proficiency.
    """

    results = {
        key: []
        for key in COMPILED_PATTERNS
    }

    lines = [
        " ".join(line.split())
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines:
        for competency, patterns in COMPILED_PATTERNS.items():

            if len(results[competency]) >= max_excerpts:
                continue

            match = next(
                (
                    pattern.search(line)
                    for pattern in patterns
                    if pattern.search(line)
                ),
                None,
            )

            if match is None:
                continue

            # Keep a short excerpt around the match.
            start = max(0, match.start() - 90)
            end = min(len(line), match.end() + 120)

            excerpt = line[start:end].strip()

            if start > 0:
                excerpt = "..." + excerpt

            if end < len(line):
                excerpt += "..."

            evidence = {
                "matched_phrase": match.group(0),
                "excerpt": excerpt,
            }

            if evidence not in results[competency]:
                results[competency].append(evidence)

    return results