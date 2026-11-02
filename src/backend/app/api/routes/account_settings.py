
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db


router = APIRouter(
    prefix="/account",
    tags=["Account Settings"],
)


class AccountSettingsUpdate(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=150,
    )


class AccountSettingsResponse(BaseModel):
    full_name: str
    email: str
    has_password: bool
    created_at: datetime


def get_account(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found.",
        )

    return user


def account_response(user: User) -> AccountSettingsResponse:
    return AccountSettingsResponse(
        full_name=user.full_name,
        email=user.email,
        has_password=bool(user.password_hash),
        created_at=user.created_at,
    )


@router.get(
    "/settings",
    response_model=AccountSettingsResponse,
)
def read_account_settings(
    response: Response,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"

    user = get_account(db, user_id)

    return account_response(user)


@router.patch(
    "/settings",
    response_model=AccountSettingsResponse,
)
def update_account_settings(
    payload: AccountSettingsUpdate,
    response: Response,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"

    user = get_account(db, user_id)

    # Reject control characters in submitted names.
    if any(
        ord(char) < 32 or ord(char) == 127
        for char in payload.full_name
    ):
        raise HTTPException(
            status_code=422,
            detail="Name contains invalid characters.",
        )

    clean_name = re.sub(
        r"\s+",
        " ",
        payload.full_name,
    ).strip()

    if not 2 <= len(clean_name) <= 150:
        raise HTTPException(
            status_code=422,
            detail="Name must contain 2 to 150 characters.",
        )

    user.full_name = clean_name

    db.commit()
    db.refresh(user)

    return account_response(user)
