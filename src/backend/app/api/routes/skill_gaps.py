from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
):
    try:
        return analyze_competency_gaps(
            db=db,
            user_id=user_id,
            career_key=career_key,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error