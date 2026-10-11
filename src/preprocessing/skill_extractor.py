import re
from pathlib import Path
import pandas as pd
from src.preprocessing.paths import PROCESSED_DATA_DIR

FINAL_ALIASES_PATH = ( PROCESSED_DATA_DIR / "final_skill_aliases.csv")

AMBIGUOUS_ALIASES = {
    "c",
    "r",
    "go",
    "make",
    "apt",
    "rust",
    "swift",
    "cargo",
    "composer",
    "cursor",
    "bun",
}
SINGLE_LETTER_ALIASES = {
    "c",
    "r",
}
TECH_CONTEXT_TERMS = {
    "skill",
    "skills",
    "technology",
    "technologies",
    "programming",
    "language",
    "languages",
    "framework",
    "frameworks",
    "database",
    "databases",
    "software",
    "development",
    "developer",
    "engineering",
    "engineer",
    "proficient",
    "experience",
    "experienced",
    "tools",
    "stack",
}
MANUAL_SKILL_ALIASES = {
    "express.js": "Express",
    "expressjs": "Express",
    "rest api": "RESTful API",
    "rest apis": "RESTful API",
    "restful api": "RESTful API",
    "restful apis": "RESTful API",
}
def load_final_aliases() -> pd.DataFrame:
    """
    Load aliases used by resume matcher.
    """
    if not FINAL_ALIASES_PATH.exists():
        raise FileNotFoundError(
            "final_skill_aliases.csv does not exist. "
            "Run final vocabulary preprocessing first."
        )

    aliases = pd.read_csv(FINAL_ALIASES_PATH)
    aliases = aliases.dropna(subset=[
            "alias",
            "canonical_skill",
        ]
    )
    aliases["alias"] = (
        aliases["alias"]
        .astype(str)
        .str.strip()
        .str.casefold()
    )
    manual_aliases = pd.DataFrame(
        [
            {
                "alias": alias,
                "canonical_skill": canonical_skill,
            }
            for alias, canonical_skill
            in MANUAL_SKILL_ALIASES.items()
        ]
    )

    aliases = pd.concat(
        [
            aliases,
            manual_aliases,
        ],
        ignore_index=True,
    )

    aliases = aliases.drop_duplicates(
        subset=[
            "alias",
            "canonical_skill",
        ]
    )
    return aliases

def normalize_resume_text(text: str) -> str:
    """
    Normalize resume text for matching while preserving
    punctuation required by technologies eg. C++,
    C#, .NET and Node.js.
    """
    text = str(text)
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u00a0": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = text.casefold()
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def build_alias_pattern(alias: str) -> re.Pattern:
    """
    Build a regex that matches a complete skill alias. Alphanumeric lookarounds prevent partial matches.
    Example:
        java should match: "Java developer" but should not match "JavaScript"
    """
    escaped = re.escape(alias)

    # Allow flexible whitespace in phrases.
    escaped = escaped.replace(
        r"\ ",
        r"\s+",
    )

    pattern = (
        rf"(?<![a-z0-9])"
        rf"{escaped}"
        rf"(?![a-z0-9])"
    )

    return re.compile(pattern,flags=re.IGNORECASE,)

def has_technical_context(
    text: str,
    start: int,
    end: int,
    window: int = 80,
) -> bool:
    """
    Determine whether an ambiguous short alias appears in a technical context.
    """
    context_start = max(
        0,
        start - window,
    )

    context_end = min(
        len(text),
        end + window,
    )

    context = text[
        context_start:context_end
    ]

    context_words = set(
        re.findall(
            r"[a-z]+",
            context,
        )
    )

    return bool(
        context_words
        & TECH_CONTEXT_TERMS
    )
def is_spaced_letter_sequence(
    text: str,
    start: int,
    end: int,
    window: int = 30,
) -> bool:
    """
    Detect whether a single-letter alias is part of
    spaced-out text such as:

        P E T E R  N Y A M U

    This prevents letters such as R or C from being
    incorrectly detected as programming languages.
    """

    context_start = max(
        0,
        start - window,
    )

    context_end = min(
        len(text),
        end + window,
    )

    context = text[
        context_start:context_end
    ]

    for match in re.finditer(
        r"(?<![a-z])(?:[a-z]\s+){2,}[a-z](?![a-z])",
        context,
    ):
        absolute_start = (
            context_start
            + match.start()
        )

        absolute_end = (
            context_start
            + match.end()
        )

        if (
            absolute_start <= start
            and absolute_end >= end
        ):
            return True

    return False

def extract_skill_matches(
    text: str,
) -> pd.DataFrame:
    """
    Extract canonical skills from resume text.

    Returns detailed matching evidence including:
    - canonical skill
    - matched alias
    - number of occurrences
    - matching rule
    """

    if not text or not str(text).strip():
        return pd.DataFrame(
            columns=[
                "canonical_skill",
                "matched_alias",
                "match_count",
                "match_rule",
            ]
        )

    aliases = load_final_aliases()

    normalized_text = normalize_resume_text(
        text
    )

    matches = []

    # Long aliases first.
    aliases = aliases.assign(
        alias_length=aliases["alias"].str.len()
    ).sort_values(
        "alias_length",
        ascending=False,
    )

    for _, row in aliases.iterrows():
        alias = row["alias"]

        canonical_skill = row[
            "canonical_skill"
        ]

        pattern = build_alias_pattern(
            alias
        )

        occurrences = list(
            pattern.finditer(
                normalized_text
            )
        )

        if not occurrences:
            continue

        # Ambiguous aliases need extra checks.
        if alias in AMBIGUOUS_ALIASES:
            valid_occurrences = []

            for match in occurrences:

                # Reject single letters that are part
                # of spaced-out text such as:
                # P E T E R
                if (
                    alias in SINGLE_LETTER_ALIASES
                    and is_spaced_letter_sequence(
                        normalized_text,
                        match.start(),
                        match.end(),
                    )
                ):
                    continue

                if has_technical_context(
                    normalized_text,
                    match.start(),
                    match.end(),
                ):
                    valid_occurrences.append(
                        match
                    )

            if not valid_occurrences:
                continue

            matches.append(
                {
                    "canonical_skill":
                        canonical_skill,
                    "matched_alias":
                        alias,
                    "match_count":
                        len(valid_occurrences),
                    "match_rule":
                        "contextual",
                }
            )

        else:
            matches.append(
                {
                    "canonical_skill":
                        canonical_skill,
                    "matched_alias":
                        alias,
                    "match_count":
                        len(occurrences),
                    "match_rule":
                        "direct",
                }
            )

    if not matches:
        return pd.DataFrame(
            columns=[
                "canonical_skill",
                "matched_alias",
                "match_count",
                "match_rule",
            ]
        )

    match_dataframe = pd.DataFrame(
        matches
    )

    aggregated = (
        match_dataframe
        .groupby(
            "canonical_skill",
            as_index=False,
        )
        .agg(
            matched_alias=(
                "matched_alias",
                lambda values:
                    ";".join(
                        sorted(
                            set(values)
                        )
                    ),
            ),
            match_count=(
                "match_count",
                "sum",
            ),
            match_rule=(
                "match_rule",
                lambda values:
                    "contextual"
                    if "contextual"
                    in set(values)
                    else "direct",
            ),
        )
    )

    return aggregated.sort_values(
        "canonical_skill"
    ).reset_index(
        drop=True
    )
def extract_skills(
    text: str,
) -> list[str]:
    #Return only canonical skill names.
    matches = extract_skill_matches(text)
    return matches["canonical_skill"].tolist()