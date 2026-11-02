
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db
from src.backend.app.services.competency_assessment_service import (
    list_assessments,
    save_assessment,
)

router = APIRouter(
    prefix="/roadmaps",
    tags=["Competency Assessments"],
)


class AssessmentUpdate(BaseModel):
    proficiency_level: Literal[
        "beginner",
        "intermediate",
        "advanced",
    ]
    notes: str | None = Field(default=None, max_length=2000)


class AssessmentResponse(BaseModel):
    competency_key: str
    proficiency_level: str
    notes: str | None
    verification_status: str = "self_reported"
    created_at: datetime
    updated_at: datetime


@router.get("/competency-assessments/{career_key}")
def get_my_assessments(
    career_key: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        records = list_assessments(db, user_id, career_key)
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return {
        "career_key": career_key,
        "assessments": [
            AssessmentResponse(
                competency_key=record.competency_key,
                proficiency_level=record.proficiency_level,
                notes=record.notes,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record in records
        ],
    }


@router.put(
    "/competency-assessments/{career_key}/{competency_key}",
    response_model=AssessmentResponse,
)
def update_my_assessment(
    payload: AssessmentUpdate,
    career_key: str,
    competency_key: str = Path(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9_]+$",
    ),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        record = save_assessment(
            db=db,
            user_id=user_id,
            career_key=career_key,
            competency_key=competency_key,
            proficiency_level=payload.proficiency_level,
            notes=payload.notes,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return AssessmentResponse(
        competency_key=record.competency_key,
        proficiency_level=record.proficiency_level,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
