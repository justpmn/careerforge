from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from src.backend.app.api.auth import get_current_user_id
from src.backend.app.database.session import get_db
from src.backend.app.services.llm_service import (LLMServiceError, generate_mentor_response)
from src.backend.app.database.models.user import User
from src.backend.app.database.models.career import Career
from src.backend.app.services.career_intent_service import (UnrecognizedCareerChange, resolve_explicit_career_change)
from src.backend.app.services.mentor_conversation_service import (list_owned_mentor_conversations, list_owned_mentor_messages,create_mentor_conversation,get_owned_conversation, save_mentor_message, make_mentor_title)
from src.backend.app.services.assessment_mentor_service import (generate_assessment_mentor_response, generate_persistent_assessment_mentor_response,)
from typing import Literal, Annotated
from pydantic import BaseModel, Field, StringConstraints, ConfigDict
from sqlalchemy import select
from src.backend.app.database.models.mentor_job import MentorGenerationJob

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
class MentorJobAccepted(BaseModel):
    job_id: int
    conversation_id: int
    career_key: str
    target_updated: bool = False


class MentorJobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    status: Literal["queued", "running", "completed", "failed"]
    response_seconds: float | None
    error: str | None
    created_at: datetime
    updated_at: datetime

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
class MentorConversationRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)

@router.post(
    "/chat",
    response_model=MentorChatResponse,
)

async def chat_with_mentor(
    request: MentorChatRequest,
    authenticated_user_id: int = Depends(get_current_user_id),
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


@router.post(
    "/jobs",
    response_model=MentorJobAccepted,
    status_code=202,
)
def queue_mentor_message(
    request: PersistentAssessmentMentorRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    message = request.message.strip()

    if not message:
        raise HTTPException(422, "Message cannot be empty.")

    try:
        user = db.scalar(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
        )

        if user is None:
            raise HTTPException(404, "User not found.")

        active_job = db.scalar(
            select(MentorGenerationJob.id)
            .where(
                MentorGenerationJob.user_id == user_id,
                MentorGenerationJob.status.in_(
                    ["queued", "running"]
                ),
            )
            .limit(1)
        )

        if active_job is not None:
            raise HTTPException(
                409,
                "The AI Mentor is still generating a response.",
            )

        requested_career = resolve_explicit_career_change(
            db=db,
            message=message,
        )

        career_key = request.career_key
        conversation_id = request.conversation_id
        target_updated = False

        if requested_career is not None:
            target_updated = (
                user.target_career_id != requested_career.id
            )

            user.target_career_id = requested_career.id
            career_key = requested_career.career_key
            conversation_id = None

        elif not career_key:
            if conversation_id is not None:
                existing = get_owned_conversation(
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id,
                )

                selected = (
                    db.get(Career, existing.career_id)
                    if existing.career_id is not None
                    else None
                )
            else:
                selected = (
                    db.get(Career, user.target_career_id)
                    if user.target_career_id is not None
                    else None
                )

            if selected is None:
                raise HTTPException(
                    422,
                    "Choose a career before sending a message.",
                )

            career_key = selected.career_key

        career = db.scalar(
            select(Career).where(
                Career.career_key == career_key
            )
        )

        if career is None:
            raise HTTPException(404, "Career not found.")

        if conversation_id is not None:
            conversation = get_owned_conversation(
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
            )

            if conversation.career_id != career.id:
                raise HTTPException(
                    422,
                    "Conversation does not match the selected career.",
                )

        else:
            conversation = create_mentor_conversation(
                db=db,
                user_id=user_id,
                career_id=career.id,
                title=make_mentor_title(message),
            )

        user_message = save_mentor_message(
            db=db,
            user_id=user_id,
            conversation_id=conversation.id,
            role="user",
            content=message,
        )

        job = MentorGenerationJob(
            user_id=user_id,
            conversation_id=conversation.id,
            user_message_id=user_message.id,
            career_key=career_key,
            status="queued",
        )

        db.add(job)
        db.flush()

        response = MentorJobAccepted(
            job_id=job.id,
            conversation_id=conversation.id,
            career_key=career_key,
            target_updated=target_updated,
        )

        db.commit()
        return response

    except (ValueError, UnrecognizedCareerChange) as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception:
        db.rollback()
        raise

@router.get(
    "/jobs",
    response_model=list[MentorJobSummary],
)
def list_mentor_jobs(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(MentorGenerationJob)
        .where(MentorGenerationJob.user_id == user_id)
        .order_by(MentorGenerationJob.id.desc())
        .limit(30)
    ).all()


@router.get(
    "/jobs/{job_id}",
    response_model=MentorJobSummary,
)
def get_mentor_job(
    job_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    job = db.scalar(
        select(MentorGenerationJob).where(
            MentorGenerationJob.id == job_id,
            MentorGenerationJob.user_id == user_id,
        )
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Mentor job not found.",
        )

    return job


@router.patch(
    "/conversations/{conversation_id}",
    response_model=MentorConversationSummary,
)
def rename_mentor_conversation(
    conversation_id: int,
    request: MentorConversationRenameRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        conversation = get_owned_conversation(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        ) from exc

    title = " ".join(request.title.split())

    if not title:
        raise HTTPException(
            status_code=422,
            detail="Conversation title cannot be empty.",
        )

    conversation.title = title

    db.commit()
    db.refresh(conversation)

    return conversation


@router.delete(
    "/conversations/{conversation_id}",
    status_code=204,
)
def delete_mentor_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        conversation = get_owned_conversation(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        ) from exc

    active_job = db.scalar(
        select(MentorGenerationJob.id)
        .where(
            MentorGenerationJob.conversation_id == conversation_id,
            MentorGenerationJob.status.in_(
                ["queued", "running"]
            ),
        )
        .limit(1)
        .with_for_update()
    )

    if active_job is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Wait for the mentor to finish before "
                "deleting this conversation."
            ),
        )

    db.delete(conversation)
    db.commit()
