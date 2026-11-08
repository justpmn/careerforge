
from functools import lru_cache
from time import perf_counter
from sqlalchemy.orm import Session
from src.recommendation.service import CareerRecommendationService
from src.backend.app.services.career_preference_service import (personalize_recommendations)
from src.backend.app.core.admin_logging import (record_system_event)


@lru_cache(maxsize=1)
def get_recommendation_service() -> CareerRecommendationService:
    """
    Initialize the Random Forest recommendation service once
    per backend process.
    """
    return CareerRecommendationService()


def analyze_career_text(
    text: str,
    top_k: int = 3,
) -> dict:
    """
    Analyze input text and return career recommendations.
    """

    started = perf_counter()

    try:
        service = get_recommendation_service()

        result = service.recommend_from_text(
            text=text,
            top_k=top_k,
        )

        record_system_event(
            category="model",
            action="recommendation_completed",
            severity="INFO",
            duration_ms=(perf_counter() - started) * 1000,
        )

        return result

    except ValueError:
        # Preserve existing validation behavior.
        raise

    except Exception as error:
        record_system_event(
            category="model",
            action="recommendation_failed",
            severity="ERROR",
            error_type=type(error).__name__,
            duration_ms=(perf_counter() - started) * 1000,
        )

        raise


def analyze_personalized_career_text(
    db: Session,
    user_id: int,
    text: str,
    top_k: int = 3,
) -> dict:
    """
    Generate Random Forest recommendations and apply
    the user's stored career preferences.
    """

    started = perf_counter()

    try:
        service = get_recommendation_service()

        career_count = len(
            service.recommender.model.classes_
        )

        result = service.recommend_from_text(
            text=text,
            top_k=career_count,
        )
        result["model_recommendations"] = [
            dict(item) for item in result["recommendations"]
        ]

        personalized = personalize_recommendations(
            db=db,
            user_id=user_id,
            recommendations=result["recommendations"],
            top_k=top_k,
        )

        result["recommendations"] = personalized

        record_system_event(
            category="model",
            action="personalized_recommendation_completed",
            severity="INFO",
            actor_user_id=user_id,
            duration_ms=(perf_counter() - started) * 1000,
        )

        return result

    except ValueError:
        raise

    except Exception as error:
        record_system_event(
            category="model",
            action="personalized_recommendation_failed",
            severity="ERROR",
            actor_user_id=user_id,
            error_type=type(error).__name__,
            duration_ms=(perf_counter() - started) * 1000,
        )

        raise
