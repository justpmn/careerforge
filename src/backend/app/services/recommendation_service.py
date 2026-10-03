from functools import lru_cache

from src.recommendation.service import (
    CareerRecommendationService,
)


@lru_cache(maxsize=1)
def get_recommendation_service() -> CareerRecommendationService:
    """
    Create the recommendation service once and reuse it.
    This prevents the Random Forest model from being loaded
    again for every API request.
    """
    return CareerRecommendationService()


def analyze_career_text(
    text: str,
    top_k: int = 3,
) -> dict:
    """
    Analyze raw text and return career recommendations.
    """
    service = get_recommendation_service()

    return service.recommend_from_text(
        text=text,
        top_k=top_k,
    )