
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db


router = APIRouter(
    prefix="/onboarding",
    tags=["Onboarding"],
)


class CareerSelectionRequest(BaseModel):
    career_key: str = Field(
        min_length=1,
        max_length=100,
    )


class CareerSelectionResponse(BaseModel):
    career_key: str | None
    

class CareerOption(BaseModel):
    id: int
    career_key: str
    name: str
    description: str | None = None
    
@router.get(
    "/careers",
    response_model=list[CareerOption],
)

@router.get(
    "/careers",
    response_model=list[CareerOption],
)
def list_available_careers(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    careers = db.scalars(
        select(Career).order_by(Career.name)
    ).all()

    return [
        CareerOption(
            id=career.id,
            career_key=career.career_key,
            name=career.name,
            description=career.description,
        )
        for career in careers
    ]

@router.get(
    "/career",
    response_model=CareerSelectionResponse,
)
def get_selected_career(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    if user.target_career_id is None:
        return CareerSelectionResponse(career_key=None)

    career = db.get(Career, user.target_career_id)

    return CareerSelectionResponse(
        career_key=career.career_key if career else None
    )


@router.put(
    "/career",
    response_model=CareerSelectionResponse,
)
def save_selected_career(
    payload: CareerSelectionRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    career = db.scalar(
        select(Career).where(
            Career.career_key == payload.career_key
        )
    )

    if career is None:
        raise HTTPException(
            status_code=404,
            detail="Career not found.",
        )

    user.target_career_id = career.id
    db.commit()

    return CareerSelectionResponse(
        career_key=career.career_key
    )
