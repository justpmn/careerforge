
from time import perf_counter

import httpx

from src.backend.app.services.llm_service import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)


def check_ollama_health() -> dict:
    """
    Check Ollama availability and configured model installation.

    Uses /api/tags rather than generating a response.
    Does not invoke LLM inference.
    """

    started = perf_counter()

    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"

    try:
        with httpx.Client(
            timeout=3.0,
            trust_env=False,
        ) as client:
            response = client.get(url)
            response.raise_for_status()

        payload = response.json()

        if not isinstance(payload, dict):
            raise ValueError("Unexpected Ollama response.")

        models = payload.get("models")

        if not isinstance(models, list):
            raise ValueError("Invalid Ollama model list.")

        installed_models = {
            name
            for model in models
            if isinstance(model, dict)
            for name in (
                model.get("name"),
                model.get("model"),
            )
            if isinstance(name, str)
        }

        latency_ms = round(
            (perf_counter() - started) * 1000,
            2,
        )

        if OLLAMA_MODEL not in installed_models:
            return {
                "status": "unhealthy",
                "message": (
                    f"Ollama is responding, but the configured "
                    f"model ({OLLAMA_MODEL}) is not installed."
                ),
                "model": OLLAMA_MODEL,
                "latency_ms": latency_ms,
            }

        return {
            "status": "healthy",
            "message": (
                "Ollama is responding and the configured "
                "model is installed."
            ),
            "model": OLLAMA_MODEL,
            "latency_ms": latency_ms,
        }

    except httpx.HTTPError as error:
        return {
            "status": "unhealthy",
            "message": "Cannot communicate with Ollama.",
            "model": OLLAMA_MODEL,
            "error_type": type(error).__name__,
            "latency_ms": None,
        }

    except (ValueError, TypeError) as error:
        return {
            "status": "unhealthy",
            "message": "Ollama returned an invalid response.",
            "model": OLLAMA_MODEL,
            "error_type": type(error).__name__,
            "latency_ms": None,
        }
