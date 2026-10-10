from functools import lru_cache
from src.recommendation.service import (CareerRecommendationService)
from sqlalchemy.orm import Session
from src.backend.app.services.career_preference_service import (personalize_recommendations)

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

def analyze_personalized_career_text(
    db: Session,
    user_id: int,
    text: str,
    top_k: int = 3,
) -> dict:
    """
    Generate RF recommendations and then apply
    the user's stored career preferences.
    """

    service = get_recommendation_service()

    # Get the complete RF ranking first.
    career_count = len(
        service.recommender.model.classes_
    )

    result = service.recommend_from_text(
        text=text,
        top_k=career_count,
    )

    personalized = personalize_recommendations(
        db=db,
        user_id=user_id,
        recommendations=result[
            "recommendations"
        ],
        top_k=top_k,
    )

    result["recommendations"] = (
        personalized
    )

    return result