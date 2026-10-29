from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db
from src.backend.app.services.llm_service import (LLMServiceError, generate_mentor_response)
from src.backend.app.database.models.user import User
from src.backend.app.database.models.career import Career
from src.backend.app.services.career_intent_service import (UnrecognizedCareerChange, resolve_explicit_career_change)
from src.backend.app.services.mentor_conversation_service import (list_owned_mentor_conversations, list_owned_mentor_messages)
from src.backend.app.services.assessment_mentor_service import (generate_assessment_mentor_response, generate_persistent_assessment_mentor_response,)
from typing import Literal, Annotated
from pydantic import BaseModel, Field, StringConstraints, ConfigDict

router = APIRouter()

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=1,
            max_length=1000,
        ),
    ]

class MentorChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )
    history: list[HistoryMessage] = Field(
        default_factory=list,
        max_length=6,
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



class PersistentAssessmentMentorRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    career_key: str | None = Field(default=None, max_length=100)
    conversation_id: int | None = Field(default=None, gt=0)


class PersistentAssessmentMentorResponse(BaseModel):
    conversation_id: int
    response: str
    career_key: str
    target_updated: bool = False


class MentorConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    career_id: int | None
    created_at: datetime
    updated_at: datetime


class MentorConversationMessage(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


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
            message=request.message.strip(),
            history=[
                item.model_dump()
                for item in request.history
            ],
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




@router.post(
    "/chat/assessment/persistent",
    response_model=PersistentAssessmentMentorResponse,
)
async def persistent_assessment_chat(
    request: PersistentAssessmentMentorRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        user = db.get(User, user_id)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found.",
            )

        requested_career = resolve_explicit_career_change(
            db=db,
            message=request.message,
        )

        active_career_key = request.career_key
        active_conversation_id = request.conversation_id
        target_updated = False

        if requested_career is not None:
            target_updated = (
                user.target_career_id != requested_career.id
            )

            # This is the actual account-level career update.
            user.target_career_id = requested_career.id
            db.flush()

            active_career_key = requested_career.career_key

            # A new career gets its own conversation,
            # avoiding mixed assessment histories.
            active_conversation_id = None

        elif not active_career_key:
            if user.target_career_id is None:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Choose a career or tell the mentor "
                        "which career you want to pursue."
                    ),
                )

            saved_career = db.get(
                Career,
                user.target_career_id,
            )

            if saved_career is None:
                raise HTTPException(
                    status_code=422,
                    detail="The selected career no longer exists.",
                )

            active_career_key = saved_career.career_key

        result = await generate_persistent_assessment_mentor_response(
            db=db,
            user_id=user_id,
            career_key=active_career_key,
            message=request.message.strip(),
            conversation_id=active_conversation_id,
        )

        db.commit()

        # Support the existing service's dictionary response.
        if isinstance(result, dict):
            conversation_id = result["conversation_id"]
            answer = result["response"]
        else:
            conversation_id = result.conversation_id
            answer = result.response

        return PersistentAssessmentMentorResponse(
            conversation_id=conversation_id,
            response=answer,
            career_key=active_career_key,
            target_updated=target_updated,
        )

    except UnrecognizedCareerChange as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except LLMServiceError as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception:
        db.rollback()
        raise

@router.get(
    "/conversations",
    response_model=list[MentorConversationSummary],
)
def get_mentor_conversations(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return list_owned_mentor_conversations(
        db=db,
        user_id=user_id,
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MentorConversationMessage],
)
def get_mentor_conversation_messages(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        return list_owned_mentor_messages(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        ) from exc
