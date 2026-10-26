from fastapi import APIRouter
from src.backend.app.api.routes.preferences import (router as preferences_router)
from src.backend.app.api.routes.health import (router as health_router)
from src.backend.app.api.routes.recommendations import (router as recommendations_router)
from src.backend.app.api.routes.skill_gaps import (router as skill_gaps_router)
from src.backend.app.api.routes.competency_evidence import (router as competency_evidence_router)
from src.backend.app.api.routes.learning_roadmaps import (router as learning_roadmaps_router)
from src.backend.app.api.routes.ai_mentor import (router as ai_mentor_router)
from src.backend.app.api.routes.auth import router as auth_router


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
    preferences_router)
api_router.include_router(
    skill_gaps_router
)
api_router.include_router(
    competency_evidence_router
)
api_router.include_router(
    learning_roadmaps_router
)
api_router.include_router(
    ai_mentor_router,
    prefix="/ai-mentor",
    tags=["AI Mentor"],
)

api_router.include_router(auth_router)

   