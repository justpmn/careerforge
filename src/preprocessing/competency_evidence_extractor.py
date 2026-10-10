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