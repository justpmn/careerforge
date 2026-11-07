from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db
from src.backend.app.services.learning_roadmap_service import (generate_learning_roadmap)

router = APIRouter(
    prefix="/roadmaps",
    tags=["Learning Roadmaps"],
)

@router.get("/users/{user_id}/careers/{career_key}")
def get_learning_roadmap(
    user_id: int,
    career_key: str,
    focus_competencies: list[str] | None = Query(
        default=None,
        description="Competency keys to prioritize.",
    ),
    optional_competencies: list[str] | None = Query(
        default=None,
        description="Competency keys to treat as optional.",
    ),
    db: Session = Depends(get_db),
    authenticated_user_id: int = Depends(get_current_user_id),
):
    # Always verify ownership before accessing user data.
    if user_id != authenticated_user_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access another user's learning roadmap.",
        )

    try:
        return generate_learning_roadmap(
            db=db,
            user_id=authenticated_user_id,
            career_key=career_key,
            focus_competencies=focus_competencies,
            optional_competencies=optional_competencies,
        )

    except ValueError as error:
        message = str(error)

        if (
            message.startswith("Unknown competencies")
            or message.startswith("A competency cannot be both")
        ):
            status_code = 400
        else:
            status_code = 404

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from error
