from functools import lru_cache

import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher

from src.preprocessing.skill_extractor import (
    AMBIGUOUS_ALIASES,
    SINGLE_LETTER_ALIASES,
    has_technical_context,
    is_spaced_letter_sequence,
    load_final_aliases,
    normalize_resume_text,
)


@lru_cache(maxsize=1)
def get_spacy_skill_matcher():
    """
    Build and cache a spaCy PhraseMatcher using
    CareerForge's cleaned skill aliases.
    """

    nlp = spacy.blank("en")

    matcher = PhraseMatcher(
        nlp.vocab,
        attr="LOWER",
    )

    aliases = load_final_aliases()

    for canonical_skill, group in aliases.groupby(
        "canonical_skill"
    ):
        patterns = [
            nlp.make_doc(alias)
            for alias in group["alias"].tolist()
        ]

        matcher.add(
            canonical_skill,
            patterns,
        )

    return nlp, matcher


def extract_spacy_skill_matches(
    text: str,
) -> pd.DataFrame:
    """
    Extract CareerForge skills using spaCy phrase matching.

    The cleaned alias vocabulary still defines what
    counts as a valid skill.
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

    normalized_text = normalize_resume_text(
        text
    )

    nlp, matcher = get_spacy_skill_matcher()

    document = nlp(
        normalized_text
    )

    matches = []

    for match_id, start, end in matcher(
        document
    ):
        span = document[
            start:end
        ]

        canonical_skill = (
            document.vocab.strings[
                match_id
            ]
        )

        matched_alias = (
            span.text
            .strip()
            .casefold()
        )

        start_char = span.start_char
        end_char = span.end_char

        if matched_alias in AMBIGUOUS_ALIASES:

            if (
                matched_alias
                in SINGLE_LETTER_ALIASES
                and is_spaced_letter_sequence(
                    normalized_text,
                    start_char,
                    end_char,
                )
            ):
                continue

            if not has_technical_context(
                normalized_text,
                start_char,
                end_char,
            ):
                continue

            match_rule = (
                "spacy_contextual"
            )

        else:
            match_rule = (
                "spacy_phrase"
            )

        matches.append(
            {
                "canonical_skill":
                    canonical_skill,
                "matched_alias":
                    matched_alias,
                "match_count":
                    1,
                "match_rule":
                    match_rule,
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
                    "spacy_contextual"
                    if "spacy_contextual"
                    in set(values)
                    else "spacy_phrase",
            ),
        )
    )

    return aggregated.sort_values(
        "canonical_skill"
    ).reset_index(
        drop=True
    )


def extract_spacy_skills(
    text: str,
) -> list[str]:
    """
    Return only canonical skill names.
    """

    matches = extract_spacy_skill_matches(
        text
    )

    return matches[
        "canonical_skill"
    ].tolist()