
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db

from src.backend.app.services.career_preference_service import (
    get_user_career_preferences,
    set_career_preference,
)


router = APIRouter(
    prefix="/preferences",
    tags=["Preferences"],
)


@router.put("/careers/{career_key}")
def update_career_preference(
    career_key: str,
    user_id: int,
    preference: str,
    authenticated_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if user_id != authenticated_user_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot modify another user's preferences.",
        )

    try:
        record = set_career_preference(
            db=db,
            user_id=authenticated_user_id,
            career_key=career_key,
            preference=preference,
        )

        return {
            "user_id": record.user_id,
            "career_key": career_key,
            "preference": record.preference,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get("/careers/{user_id}")
def read_career_preferences(
    user_id: int,
    authenticated_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    if user_id != authenticated_user_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another user's preferences.",
        )

    return get_user_career_preferences(
        db=db,
        user_id=authenticated_user_id,
    )
