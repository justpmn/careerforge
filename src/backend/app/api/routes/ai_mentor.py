from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db
from src.backend.app.services.llm_service import (
    LLMServiceError,
    generate_mentor_response,
)
from src.backend.app.services.assessment_mentor_service import (
    generate_assessment_mentor_response,
)

router = APIRouter()

class MentorChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )


class AssessmentMentorRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )
    career_key: str = Field(
        min_length=1,
        max_length=100,
    )

class MentorChatResponse(BaseModel):
    response: str


@router.post(
    "/chat",
    response_model=MentorChatResponse,
)
async def chat_with_mentor(
    request: MentorChatRequest,
) -> MentorChatResponse:

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


@router.post(
    "/chat/assessment",
    response_model=MentorChatResponse,
)
async def chat_with_assessment(
    request: AssessmentMentorRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> MentorChatResponse:

    if not request.message.strip():
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty.",
        )

    try:
        answer = await generate_assessment_mentor_response(
            db=db,
            user_id=user_id,
            career_key=request.career_key,
            message=request.message.strip(),
        )

        return MentorChatResponse(response=answer)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except LLMServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail="AI mentor is temporarily unavailable.",
        ) from exc
