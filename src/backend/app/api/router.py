from fastapi import APIRouter
from src.backend.app.api.routes.preferences import (router as preferences_router)
from src.backend.app.api.routes.health import (router as health_router)
from src.backend.app.api.routes.recommendations import (router as recommendations_router)
from src.backend.app.api.routes.skill_gaps import (
    router as skill_gaps_router,
)
api_router = APIRouter(
    prefix="/api"
)

api_router.include_router(
    health_router
)

api_router.include_router(
    recommendations_router
)
api_router.include_router(
    preferences_router
)
api_router.include_router(
    skill_gaps_router
)   