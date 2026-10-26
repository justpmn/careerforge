from fastapi import FastAPI
from src.backend.app.api.router import api_router
from src.backend.app.core.config import settings
from starlette.middleware.sessions import SessionMiddleware
from src.backend.app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)
if (
    not settings.oauth_state_secret_key
    or len(settings.oauth_state_secret_key.encode("utf-8")) < 32
):
    raise RuntimeError(
        "A secure OAUTH_STATE_SECRET_KEY must be configured."
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.oauth_state_secret_key,
    session_cookie="careerforge_oauth_state",
    same_site="lax",
    https_only=False,  # Local HTTP only
    max_age=600,
)

app.include_router(api_router)

@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} is running"
    }