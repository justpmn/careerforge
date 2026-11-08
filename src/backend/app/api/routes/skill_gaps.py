
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db

from src.backend.app.services.competency_gap_service import (
    analyze_competency_gaps,
)


router = APIRouter(
    prefix="/skill-gaps",
    tags=["Skill Gaps"],
)


@router.get("/users/{user_id}/careers/{career_key}")
def get_skill_gaps(
    user_id: int,
    career_key: str,
    db: Session = Depends(get_db),
    authenticated_user_id: int = Depends(get_current_user_id),
):
    # Prevent cross-user access to competency information.
    if user_id != authenticated_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access another user's competency gaps.",
        )

    try:
        return analyze_competency_gaps(
            db=db,
            user_id=authenticated_user_id,
            career_key=career_key,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
