
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.backend.app.core.security import hash_password, verify_password
from src.backend.app.core.tokens import create_access_token
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=2,
            max_length=150,
        ),
    ]

    email: EmailStr = Field(max_length=255)

    password: str = Field(
        min_length=12,
        max_length=128,
    )


class RegisterResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    normalized_email = request.email.strip().lower()

    existing_user = db.scalar(
        select(User).where(
            func.lower(func.btrim(User.email))
            == normalized_email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    user = User(
        full_name=request.full_name,
        email=normalized_email,
        password_hash=hash_password(request.password),
        role="user",
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError as exc:
        db.rollback()

        constraint_name = getattr(
            getattr(exc.orig, "diag", None),
            "constraint_name",
            None,
        )

        if constraint_name == "uq_users_email_normalized":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            ) from exc

        raise

    except Exception:
        db.rollback()
        raise

    return RegisterResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    normalized_email = request.email.strip().lower()

    user = db.scalar(
        select(User).where(
            func.lower(func.btrim(User.email)) == normalized_email
        )
    )

    if user is None or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user_id=user.id,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
    )

