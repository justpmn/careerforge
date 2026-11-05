from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db
from src.backend.app.api.auth import get_admin_enrollment_user_id

def require_admin(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return user

def require_admin_enrollment(
    user_id: int = Depends(get_admin_enrollment_user_id),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    return user