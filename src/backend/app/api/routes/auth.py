import hmac
import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.backend.app.core.security import hash_password, verify_password
from src.backend.app.core.tokens import create_access_token, decode_access_token
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from src.backend.app.core.config import settings
from src.backend.app.api.auth import (create_csrf_token, get_current_user_id, validate_csrf_token)


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

class CurrentUserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    onboarding_completed: bool

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
    response: Response,
    db: Session = Depends(get_db),
):
    normalized_email = request.email.strip().lower()

    user = db.scalar(
        select(User).where(
            func.lower(func.btrim(User.email)) == normalized_email
        )
    )

    if (
        user is None
        or user.password_hash is None
        or not verify_password(
            request.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user_id=user.id)

    max_age = settings.jwt_access_token_expire_minutes * 60

    response.set_cookie(
        key="careerforge_session",
        value=access_token,
        httponly=True,
        secure=False,  # Local development only
        samesite="lax",
        path="/api",
        max_age=max_age,
    )

    # CSRF token accessible to the frontend
    response.set_cookie(
        key="csrf_token",
        value=create_csrf_token(access_token),
        httponly=False,
        secure=False,  # Local development only
        samesite="lax",
        path="/",
        max_age=max_age,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
    )
    

@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def get_authenticated_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )

    return CurrentUserResponse(
        id=str(user.id),
        name=user.full_name,
        email=user.email,
        onboarding_completed=user.onboarding_completed,
    )


@router.post(
    "/onboarding/complete",
    status_code=status.HTTP_204_NO_CONTENT,
)
def complete_onboarding(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    user.onboarding_completed = True
    db.commit()

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout_user(
    request: Request,
    response: Response,
):
    session_token = request.cookies.get("careerforge_session")

    if session_token:
        validate_csrf_token(request, session_token)

    response.delete_cookie(
        key="careerforge_session",
        path="/api",
    )

    response.delete_cookie(
        key="csrf_token",
        path="/",
    )
