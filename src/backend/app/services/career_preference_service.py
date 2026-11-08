from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.database.models.career import Career
from src.backend.app.database.models.user import User
from src.backend.app.database.models.user_career_preference import (
    UserCareerPreference,
)


VALID_PREFERENCES = {
    "preferred",
    "avoid",
}


def set_career_preference(
    db: Session,
    user_id: int,
    career_key: str,
    preference: str,
) -> UserCareerPreference:
    if preference not in VALID_PREFERENCES:
        raise ValueError(
            "Preference must be 'preferred' or 'avoid'."
        )

    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise ValueError(
            f"User {user_id} does not exist."
        )

    career = db.scalar(
        select(Career).where(
            Career.career_key == career_key
        )
    )

    if career is None:
        raise ValueError(
            f"Career '{career_key}' does not exist."
        )

    existing = db.scalar(
        select(UserCareerPreference).where(
            UserCareerPreference.user_id == user_id,
            UserCareerPreference.career_id == career.id,
        )
    )

    if existing:
        existing.preference = preference
        db.commit()
        db.refresh(existing)
        return existing

    record = UserCareerPreference(
        user_id=user_id,
        career_id=career.id,
        preference=preference,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record

def remove_career_preference(
    db: Session,
    user_id: int,
    career_key: str,
) -> bool:
    career = db.scalar(
        select(Career).where(Career.career_key == career_key)
    )

    if career is None:
        raise ValueError(f"Career '{career_key}' does not exist.")

    record = db.scalar(
        select(UserCareerPreference).where(
            UserCareerPreference.user_id == user_id,
            UserCareerPreference.career_id == career.id,
        )
    )

    if record is None:
        return False

    db.delete(record)
    db.commit()
    return True

def get_user_career_preferences(
    db: Session,
    user_id: int,
) -> dict[str, list[str]]:
    rows = db.execute(
        select(
            Career.career_key,
            UserCareerPreference.preference,
        )
        .join(
            UserCareerPreference,
            UserCareerPreference.career_id == Career.id,
        )
        .where(
            UserCareerPreference.user_id == user_id
        )
    ).all()

    preferred = []
    avoid = []

    for career_key, preference in rows:
        if preference == "preferred":
            preferred.append(career_key)

        elif preference == "avoid":
            avoid.append(career_key)

    return {
        "preferred": preferred,
        "avoid": avoid,
    }
def personalize_recommendations(
    db: Session,
    user_id: int,
    recommendations: list[dict],
    top_k: int = 3,
) -> list[dict]:
    """
    Apply stored user career preferences to
    Random Forest recommendations.

    - avoided careers are removed
    - preferred careers are surfaced first
    - RF scores are never modified
    """

    preferences = get_user_career_preferences(
        db=db,
        user_id=user_id,
    )

    preferred = set(
        preferences["preferred"]
    )

    avoided = set(
        preferences["avoid"]
    )

    # Remove careers the user does not want.
    visible = [
        recommendation
        for recommendation in recommendations
        if recommendation["career_key"]
        not in avoided
    ]

    # Preferred careers come first.
    # Within each group, preserve RF score order.
    visible.sort(
        key=lambda recommendation: (
            0
            if recommendation["career_key"]
            in preferred
            else 1,
            -recommendation["score"],
        )
    )

    # Recalculate visible ranks.
    personalized = []

    for rank, recommendation in enumerate(
        visible[:top_k],
        start=1,
    ):
        personalized.append(
            {
                "rank": rank,
                "career_key":
                    recommendation["career_key"],
                "score":
                    recommendation["score"],
            }
        )

    return personalized