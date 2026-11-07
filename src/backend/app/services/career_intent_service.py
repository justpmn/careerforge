
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.career import Career


class UnrecognizedCareerChange(ValueError):
    pass


CHANGE_PATTERNS = (
    r"(?:please\s+)?(?:i\s+want|i\s+would\s+like|i'd\s+like)"
    r"\s+to\s+(?:become|be|work\s+as|pursue|switch\s+to|"
    r"move\s+into|focus\s+on|do)\s+(?:an?\s+)?(?P<career>.+)",

    r"(?:please\s+)?(?:i\s+want|i\s+would\s+like|i'd\s+like)"
    r"\s+to\s+(?:change|set|update|switch)\s+my\s+"
    r"(?:target\s+)?career\s+to\s+(?:an?\s+)?(?P<career>.+)",

    r"(?:please\s+)?(?:change|set|update|switch)\s+"
    r"(?:my\s+)?(?:target\s+)?career\s+to\s+"
    r"(?:an?\s+)?(?P<career>.+)",

    r"(?:please\s+)?(?:set|make)\s+(?P<career>.+?)"
    r"\s+as\s+my\s+(?:target\s+)?career",
)


def normalize_career_name(value: str) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        value.casefold(),
    ).strip()


def resolve_explicit_career_change(
    db: Session,
    message: str,
) -> Career | None:
    text = message.strip()

    # Questions about careers must not change account preferences.
    if text.endswith("?"):
        return None

    text = text.rstrip(".!")

    requested_name = None

    for pattern in CHANGE_PATTERNS:
        match = re.fullmatch(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            requested_name = match.group("career").strip()
            break

    if requested_name is None:
        return None

    requested_name = re.sub(
        r"\s+(?:please|for now|from now on)$",
        "",
        requested_name,
        flags=re.IGNORECASE,
    ).strip()

    requested_normalized = normalize_career_name(
        requested_name
    )

    careers = db.scalars(select(Career)).all()

    matches = [
        career
        for career in careers
        if requested_normalized in {
            normalize_career_name(career.name),
            normalize_career_name(career.career_key),
        }
    ]

    if len(matches) != 1:
        raise UnrecognizedCareerChange(
            f"Could not uniquely identify '{requested_name}' "
            "in CareerForge's available careers. "
            "Please use an available career name."
        )

    return matches[0]
