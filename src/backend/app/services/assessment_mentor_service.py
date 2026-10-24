
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.backend.app.services.competency_gap_service import (analyze_competency_gaps)
from src.backend.app.services.ai_mentor_context_service import (build_mentor_context)
from src.backend.app.services.llm_service import (generate_mentor_response)
from src.backend.app.database.models.career import Career
from src.backend.app.services.mentor_conversation_service import (
    create_mentor_conversation,
    get_owned_conversation,
    get_recent_mentor_history,
    save_mentor_message,
)


async def generate_assessment_mentor_response(
    db: Session,
    user_id: int,
    career_key: str,
    message: str,
) -> str:

    assessment = analyze_competency_gaps(
        db=db,
        user_id=user_id,
        career_key=career_key,
    )

    context = build_mentor_context(assessment)

    response = await generate_mentor_response(
        message=message,
        context=context,
    )

    return response




async def generate_persistent_assessment_mentor_response(
    db: Session,
    user_id: int,
    career_key: str,
    message: str,
    conversation_id: int | None = None,
) -> dict:

    career_id = db.scalar(
        select(Career.id).where(
            Career.career_key == career_key
        )
    )

    if career_id is None:
        raise ValueError("Career not found.")

    history = []

    if conversation_id is not None:
        conversation = get_owned_conversation(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        if conversation.career_id != career_id:
            raise ValueError(
                "Conversation does not belong to the requested career."
            )

        history = get_recent_mentor_history(
            db=db,
            user_id=user_id,
            conversation_id=conversation_id,
        )

    assessment = analyze_competency_gaps(
        db=db,
        user_id=user_id,
        career_key=career_key,
    )

    context = build_mentor_context(assessment)

    response = await generate_mentor_response(
        message=message,
        context=context,
        history=history,
    )

    if conversation_id is None:
        conversation = create_mentor_conversation(
            db=db,
            user_id=user_id,
            career_id=career_id,
            title=f"{assessment['career_name']} Assessment",
        )

        conversation_id = conversation.id

    save_mentor_message(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        role="user",
        content=message,
    )

    save_mentor_message(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
        role="assistant",
        content=response,
    )

    return {
        "conversation_id": conversation_id,
        "response": response,
    }
