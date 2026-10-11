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