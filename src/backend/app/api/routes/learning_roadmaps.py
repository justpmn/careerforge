
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.backend.app.database.session import get_db
from src.backend.app.services.learning_roadmap_service import (
    generate_learning_roadmap,
)


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
        description="Competency keys to treat as optional in this roadmap.",
    ),
    db: Session = Depends(get_db),
):
    try:
        return generate_learning_roadmap(
            db=db,
            user_id=user_id,
            career_key=career_key,
            focus_competencies=focus_competencies,
            optional_competencies=optional_competencies,
        )

    except ValueError as error:
        message = str(error)

        # Invalid personalization choices are client errors.
        if (
            message.startswith("Unknown competencies")
            or message.startswith(
                "A competency cannot be both"
            )
        ):
            status_code = 400
        else:
            # The underlying service raises ValueError
            # for missing users, careers, or profiles.
            status_code = 404

        raise HTTPException(
            status_code=status_code,
            detail=message,
        ) from error
