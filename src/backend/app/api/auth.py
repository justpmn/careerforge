
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.backend.app.core.tokens import decode_access_token
from src.backend.app.database.models.user import User
from src.backend.app.database.session import get_db


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> int:

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        user_id = decode_access_token(
            credentials.credentials
        )
    except ValueError as exc:
        raise unauthorized from exc

    user = db.get(User, user_id)

    if user is None:
        raise unauthorized

    return user.id
