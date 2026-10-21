from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.backend.app.services.llm_service import (
    LLMServiceError,
    generate_mentor_response,
)
router = APIRouter()


class MentorChatRequest(BaseModel):
    """
    Defines the information required from the user.
    """

    message: str = Field(
        min_length=1,
        max_length=2000,
        description="The user's career-related question.",
    )


class MentorChatResponse(BaseModel):
    """
    Defines the response returned by our AI mentor.
    """

    response: str


@router.post("/chat", response_model=MentorChatResponse)
async def chat_with_mentor(
    request: MentorChatRequest,
) -> MentorChatResponse:
    """
    Receive a message and generate an AI mentor response.

    The endpoint delegates LLM communication to llm_service,
    keeping API handling separate from business logic.
    """

    if not request.message.strip():
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )

    try:
        answer = await generate_mentor_response(
            request.message.strip()
        )
        return MentorChatResponse(response=answer)

    except LLMServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail="AI mentor is temporarily unavailable.",
        ) from exc
