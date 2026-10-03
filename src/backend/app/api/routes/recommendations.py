from fastapi import (
    APIRouter,
    HTTPException,
)

from src.backend.app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)

from src.backend.app.services.recommendation_service import (
    analyze_career_text,
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.post(
    "/analyze",
    response_model=RecommendationResponse,
)
def analyze_recommendation(
    request: RecommendationRequest,
):
    try:
        return analyze_career_text(
            text=request.text,
            top_k=request.top_k,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error