
import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.backend.app.api.auth import get_current_user_id
from src.backend.app.api.admin_auth import require_admin
from src.backend.app.core.security import verify_password
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from src.backend.app.services.admin_mfa_verification import (
    verify_and_consume_admin_totp,
)

logger = logging.getLogger(__name__)

account_router = APIRouter(prefix="/account", tags=["Account"])
admin_users_router = APIRouter(prefix="/admin/users", tags=["Administration"])


class DeleteMyAccount(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    confirmation: Literal["DELETE"]


class ModerationRequest(BaseModel):
    totp_code: str = Field(pattern=r"^[0-9]{6}$")
    reason: str = Field(default="", max_length=500)


class AdminDeleteRequest(BaseModel):
    totp_code: str = Field(pattern=r"^[0-9]{6}$")
    confirm_email: EmailStr


def delete_account(db: Session, user_id: int) -> None:
    try:
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Account deletion blocked by database constraints: %s", user_id)
        raise HTTPException(
            status_code=409,
            detail="Account deletion is blocked by dependent records. No data was deleted.",
        ) from exc


def get_manageable_user(db: Session, target_id: int, actor_id: int) -> User:
    target = db.scalar(
        select(User)
        .where(User.id == target_id)
        .with_for_update()
    )

    if target is None:
        raise HTTPException(404, "User not found.")

    if target.id == actor_id or target.role == "admin":
        raise HTTPException(403, "Administrator accounts cannot be managed here.")

    return target


@account_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    payload: DeleteMyAccount,
    response: Response,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.id == user_id).with_for_update()
    )

    if user is None:
        raise HTTPException(401, "Account no longer exists.")

    if user.role == "admin":
        raise HTTPException(403, "Administrator accounts require a separate removal procedure.")

    if user.email.strip().lower() != payload.email.strip().lower():
        raise HTTPException(400, "Email confirmation does not match.")

    if user.password_hash is None:
        raise HTTPException(
            400,
            "Password authentication is required to delete this account.",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(403, "Incorrect password.")

    delete_account(db, user.id)

    response.delete_cookie("careerforge_session", path="/api")
    response.delete_cookie("csrf_token", path="/")
    logger.info("User account %s deleted by its owner.", user_id)


@admin_users_router.get("")
def list_users(
    q: str = Query(default="", max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    conditions = []
    if q.strip():
        term = f"%{q.strip()}%"
        conditions.append(
            or_(User.email.ilike(term), User.full_name.ilike(term))
        )

    total = db.scalar(
        select(func.count()).select_from(User).where(*conditions)
    ) or 0

    users = db.scalars(
        select(User)
        .where(*conditions)
        .order_by(User.created_at.desc(), User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at,
                "suspended_at": user.suspended_at,
                "suspension_reason": user.suspension_reason,
            }
            for user in users
        ],
    }


@admin_users_router.post("/{target_id}/suspend")
def suspend_user(
    target_id: int,
    payload: ModerationRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    verify_and_consume_admin_totp(
        db=db, user_id=admin.id, code=payload.totp_code
    )

    target = get_manageable_user(db, target_id, admin.id)

    if target.suspended_at is not None:
        raise HTTPException(409, "Account is already suspended.")

    target.suspended_at = datetime.now(timezone.utc)
    target.suspension_reason = payload.reason.strip() or None
    db.commit()

    logger.info("Admin %s suspended user %s.", admin.id, target_id)
    return {"message": "Account suspended."}


@admin_users_router.post("/{target_id}/reactivate")
def reactivate_user(
    target_id: int,
    payload: ModerationRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    verify_and_consume_admin_totp(
        db=db, user_id=admin.id, code=payload.totp_code
    )

    target = get_manageable_user(db, target_id, admin.id)

    if target.suspended_at is None:
        raise HTTPException(409, "Account is already active.")

    target.suspended_at = None
    target.suspension_reason = None
    db.commit()

    logger.info("Admin %s reactivated user %s.", admin.id, target_id)
    return {"message": "Account reactivated."}


@admin_users_router.delete("/{target_id}", status_code=204)
def admin_delete_user(
    target_id: int,
    payload: AdminDeleteRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    verify_and_consume_admin_totp(
        db=db, user_id=admin.id, code=payload.totp_code
    )

    target = get_manageable_user(db, target_id, admin.id)

    if target.email.strip().lower() != payload.confirm_email.strip().lower():
        raise HTTPException(400, "Email confirmation does not match.")

    delete_account(db, target.id)
    logger.info("Admin %s deleted user %s.", admin.id, target_id)
