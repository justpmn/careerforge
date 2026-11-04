from fastapi import FastAPI, Request
from src.backend.app.api.router import api_router
from starlette.middleware.sessions import SessionMiddleware
from src.backend.app.core.config import settings
from src.backend.app.core.admin_logging import record_system_event

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

@app.middleware("http")
async def log_application_failures(request: Request, call_next):
    try:
        response = await call_next(request)

    except Exception as error:
        route = request.scope.get("route")
        route_pattern = getattr(route, "path", None)

        record_system_event(
            category="application",
            action="unhandled_exception",
            severity="ERROR",
            status_code=500,
            error_type=type(error).__name__,
            route=route_pattern,
        )

        raise

    if response.status_code >= 500:
        route = request.scope.get("route")
        route_pattern = getattr(route, "path", None)

        record_system_event(
            category="application",
            action="server_error_response",
            severity="ERROR",
            status_code=response.status_code,
            route=route_pattern,
        )

    return response

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