import os
import httpx

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434"
).rstrip("/")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")

SYSTEM_PROMPT = """
You are CareerForge's AI Career Mentor.

Your purpose is to provide accurate, practical,
and personalized career guidance.

Follow these rules:
1. Use only the user information provided.
2. Never invent career predictions or assessment results.
3. Do not assume users lack skills without evidence.
4. Acknowledge missing assessment information.
5. Explain career recommendations clearly.
6. Suggest actionable learning steps.
7. Keep your responses concise and professional.
"""


class LLMServiceError(Exception):
    """Represents an error communicating with the LLM."""


async def generate_mentor_response(message: str) -> str:
    """
    Send a user message to Ollama and return the AI response.

    Args:
        message: The user's career-related question.

    Returns:
        The AI mentor's generated response.

    Raises:
        LLMServiceError: If Ollama cannot generate a response.
    """

   
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "think": False,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": message,
            },
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            response.raise_for_status()

    except httpx.RequestError as exc:
        raise LLMServiceError(
            "Could not connect to Ollama."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise LLMServiceError(
            f"Ollama returned HTTP {exc.response.status_code}."
        ) from exc
    try:
        content = response.json()["message"]["content"].strip()

    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise LLMServiceError(
            "Invalid response received from Ollama."
        ) from exc

    if not content:
        raise LLMServiceError("Ollama returned an empty response.")

    return content
