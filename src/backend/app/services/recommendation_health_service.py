
from time import perf_counter

from src.backend.app.services.recommendation_service import (
    get_recommendation_service,
)


def check_recommendation_model_health() -> dict:
    """
    Verify the recommendation service and its trained model.

    Does not run a prediction or modify model data.
    The first call may initialize the cached model service.
    """

    started = perf_counter()

    try:
        service = get_recommendation_service()

        recommender = service.recommender
        model = recommender.model

        if model is None:
            raise RuntimeError("Model is not initialized.")

        predict_method = getattr(
            model,
            "predict_proba",
            None,
        )

        if not callable(predict_method):
            raise RuntimeError(
                "Loaded model does not support probability prediction."
            )

        # The current recommendation service uses classes_
        # to determine the available career categories.
        classes = getattr(model, "classes_", None)

        if classes is None:
            raise RuntimeError(
                "Loaded model does not expose career classes."
            )

        class_count = len(classes)

        if class_count == 0:
            raise RuntimeError(
                "Loaded model has no career classes."
            )

        latency_ms = round(
            (perf_counter() - started) * 1000,
            2,
        )

        return {
            "status": "healthy",
            "message": (
                "Trained career recommendation model "
                "loaded and exposes its prediction interface."
            ),
            "model": "CareerForge Random Forest",
            "career_classes": class_count,
            "latency_ms": latency_ms,
        }

    except Exception as error:
        return {
            "status": "unhealthy",
            "message": (
                "Recommendation service or model "
                "initialization failed."
            ),
            "model": "CareerForge Random Forest",
            "error_type": type(error).__name__,
            "latency_ms": round(
                (perf_counter() - started) * 1000,
                2,
            ),
        }
