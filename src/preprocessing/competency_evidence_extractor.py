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