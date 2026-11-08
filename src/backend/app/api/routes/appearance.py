
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db


router = APIRouter(
    prefix="/appearance",
    tags=["Appearance"],
)


class AppearancePreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appearance: Literal["cozy", "neon"]
    cozy_theme: Literal["light", "dark"]


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return user


@router.get("", response_model=AppearancePreferences)
def get_appearance(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = get_user(db, user_id)

    return AppearancePreferences(
        appearance=user.appearance,
        cozy_theme=user.cozy_theme,
    )


@router.put("", response_model=AppearancePreferences)
def update_appearance(
    payload: AppearancePreferences,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = get_user(db, user_id)

    user.appearance = payload.appearance
    user.cozy_theme = payload.cozy_theme

    db.commit()
    db.refresh(user)

    return AppearancePreferences(
        appearance=user.appearance,
        cozy_theme=user.cozy_theme,
    )
