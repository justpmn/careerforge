
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db
from src.backend.app.services.competency_evidence_service import (
    create_competency_evidence,
    get_competency_evidence,
)


router = APIRouter(
    prefix="/users",
    tags=["Competency Evidence"],
)


class CompetencyEvidenceCreate(BaseModel):
    competency_key: str = Field(min_length=1)

    evidence_type: Literal[
        "project",
        "experience",
        "certification",
    ]

    description: str = Field(
        min_length=1,
        max_length=5000,
    )


@router.post(
    "/{user_id}/careers/{career_key}/competency-evidence",
    status_code=201,
)
def submit_competency_evidence(
    user_id: int,
    career_key: str,
    payload: CompetencyEvidenceCreate,
    authenticated_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # Ensure users can only submit their own evidence
    if user_id != authenticated_user_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot submit evidence for another user.",
        )

    try:
        evidence = create_competency_evidence(
            db=db,
            user_id=authenticated_user_id,
            career_key=career_key,
            competency_key=payload.competency_key,
            evidence_type=payload.evidence_type,
            description=payload.description,
        )

        return {
            "id": evidence.id,
            "user_id": evidence.user_id,
            "career_key": career_key,
            "competency_key": evidence.competency_key,
            "evidence_type": evidence.evidence_type,
            "description": evidence.description,
            "verification_status": evidence.verification_status,
            "created_at": evidence.created_at,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get(
    "/{user_id}/careers/{career_key}/competency-evidence"
)
def list_competency_evidence(
    user_id: int,
    career_key: str,
    authenticated_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # Ensure users can only access their own evidence
    if user_id != authenticated_user_id:
        raise HTTPException(
            status_code=403,
            detail="You cannot access another user's competency evidence.",
        )

    try:
        records = get_competency_evidence(
            db=db,
            user_id=authenticated_user_id,
            career_key=career_key,
        )

        return {
            "user_id": authenticated_user_id,
            "career_key": career_key,
            "evidence": [
                {
                    "id": record.id,
                    "competency_key": record.competency_key,
                    "evidence_type": record.evidence_type,
                    "description": record.description,
                    "verification_status": record.verification_status,
                    "created_at": record.created_at,
                }
                for record in records
            ],
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
