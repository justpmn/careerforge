
import json
from copy import deepcopy
from pathlib import Path

from src.backend.app.services.competency_templates import (
    COMMON_COMPETENCIES,
)
from src.preprocessing.competency_evidence_extractor import (
    COMPETENCY_PATTERNS,
)


PROFILE_DIR = (
    Path(__file__).resolve().parents[1]
    / "competency_profiles"
)


def validate_group(group: dict, career_key: str):
    """Validate one expanded competency group."""

    required = {"key", "name", "level", "any_of"}

    if not required.issubset(group):
        raise ValueError(
            f"{career_key}: missing group fields "
            f"{required - set(group)}"
        )

    if not all(
        isinstance(group[field], str) and group[field].strip()
        for field in ("key", "name", "level")
    ):
        raise ValueError(
            f"{career_key}: invalid competency fields"
        )

    if group["level"] not in {"core", "supporting"}:
        raise ValueError(
            f"{career_key}: invalid level in {group['key']}"
        )

    skills = group["any_of"]

    if (
        not isinstance(skills, list)
        or any(
            not isinstance(skill, str) or not skill.strip()
            for skill in skills
        )
        or len(skills) != len(set(skills))
    ):
        raise ValueError(
            f"{career_key}: invalid skills in {group['key']}"
        )

    assessment = group.get("assessment", "skill_match")

    if assessment == "manual_review":
        if group["key"] not in COMPETENCY_PATTERNS:
            raise ValueError(
                f"{career_key}: no evidence patterns "
                f"for {group['key']}"
            )

        if skills:
            raise ValueError(
                f"{career_key}: manual-review group "
                f"{group['key']} should have no skill list"
            )

    elif assessment == "skill_match":
        if not skills:
            raise ValueError(
                f"{career_key}: {group['key']} has no skills"
            )

    else:
        raise ValueError(
            f"{career_key}: unknown assessment {assessment}"
        )


def load_profile(path: Path) -> tuple[str, list[dict]]:
    """Load, expand and validate a career profile."""

    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    career_key = data["career_key"]

    if career_key != path.stem:
        raise ValueError(
            f"Profile key does not match filename: {path.name}"
        )

    if data.get("version") != 1:
        raise ValueError(
            f"{career_key}: unsupported profile version"
        )

    groups = data.get("groups")

    if not isinstance(groups, list) or not groups:
        raise ValueError(
            f"{career_key}: invalid or empty group list"
        )

    expanded = []
    seen_keys = set()

    for entry in groups:
        if not isinstance(entry, dict):
            raise ValueError(
                f"{career_key}: invalid group entry"
            )

        if "template" in entry:
            if set(entry) != {"template"}:
                raise ValueError(
                    f"{career_key}: invalid template reference"
                )

            template_key = entry["template"]

            if template_key not in COMMON_COMPETENCIES:
                raise ValueError(
                    f"{career_key}: unknown template {template_key}"
                )

            group = deepcopy(
                COMMON_COMPETENCIES[template_key]
            )
        else:
            group = deepcopy(entry)

        validate_group(group, career_key)

        if group["key"] in seen_keys:
            raise ValueError(
                f"{career_key}: duplicate group {group['key']}"
            )

        seen_keys.add(group["key"])
        expanded.append(group)

    return career_key, expanded


def load_all_profiles() -> dict[str, list[dict]]:
    """Load all available career competency profiles."""

    profiles = {}

    for path in sorted(PROFILE_DIR.glob("*.json")):
        career_key, groups = load_profile(path)

        if career_key in profiles:
            raise ValueError(
                f"Duplicate career profile: {career_key}"
            )

        profiles[career_key] = groups

    if not profiles:
        raise ValueError("No career profiles found.")

    return profiles
