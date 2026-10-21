from fastapi import HTTPException, status

def get_current_user_id() -> int:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is required.",
    )
