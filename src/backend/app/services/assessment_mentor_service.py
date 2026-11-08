
import logging
import re
from time import perf_counter
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.backend.app.database.models.career import Career
from src.backend.app.services.competency_gap_service import (analyze_competency_gaps)
from src.backend.app.services.ai_mentor_context_service import (build_mentor_context)
from src.backend.app.services.llm_service import (generate_mentor_response)
from src.backend.app.services.mentor_conversation_service import (create_mentor_conversation, get_owned_conversation, get_recent_mentor_history, save_mentor_message, make_mentor_title)
from src.backend.app.services.careerforge_account_context_service import (build_account_mentor_context)

logger = logging.getLogger("uvicorn.error")


# Detect requests for courses and learning materials.
LEARNING_RESOURCE_PATTERNS = (
    r"\bwhere\b.{0,80}\b(?:learn|study|course|training)\b",
    r"\bhow\b.{0,80}\b(?:learn|study)\b",
    r"\b(?:courses?|tutorials?|learning resources?|"
    r"learning materials?|certifications?|study materials?)\b",
    r"\b(?:send|give|share|recommend|find)\b"
    r".{0,60}\b(?:links?|resources?|courses?|videos?)\b",
)


RESOURCE_FOLLOWUP_PATTERN = re.compile(
    r"\b("
    r"which one|"
    r"which course|"
    r"which resource|"
    r"which link|"
    r"where should i start|"
    r"what should i start with|"
    r"which should i start with|"
    r"which is best|"
    r"which one first"
    r")\b",
    flags=re.IGNORECASE,
)


def is_learning_resource_question(message: str) -> bool:
    return any(
        re.search(pattern, message, flags=re.IGNORECASE)
        for pattern in LEARNING_RESOURCE_PATTERNS
    )


def should_include_learning_resources(
    message: str,
    history: list[dict],
) -> bool:
    # Direct request for courses or resources.
    if is_learning_resource_question(message):
        return True

    # Not a recognized resource follow-up.
    if not RESOURCE_FOLLOWUP_PATTERN.search(message):
        return False

    # Check previous user questions for resource requests.
    recent_user_messages = [
        item.get("content", "")
        for item in history[-4:]
        if item.get("role") == "user"
    ]

    return any(
        is_learning_resource_question(previous)
        for previous in recent_user_messages
    )

def build_grounded_mentor_context(
    db: Session,
    user_id: int,
    career_key: str,
    assessment: dict,
    include_resources: bool,
    message: str,
) -> dict:
    account_context = build_account_mentor_context(
        db=db,
        user_id=user_id,
        career_key=career_key,
        include_resources=include_resources,
    )

    if is_cv_ranking_question(message):
        return {
            "focus": "saved_cv_recommendations",
            "recommendations": account_context["recommendations"],
            "career_preferences": account_context["career_preferences"],
            "instructions": (
                "Answer the user's question about saved CV "
                "recommendations directly. Name the ranked careers "
                "and compare their Random Forest scores with "
                "documented skill coverage. These metrics measure "
                "different things and neither verifies career "
                "readiness. Do not substitute a competency "
                "assessment. If rankings are unavailable, say so."
            ),
        }

    assessment_context = build_mentor_context(
        assessment,
        include_resources=False,
    )

    competencies = assessment_context.get("competencies", [])

    assessment_context["competencies"] = competencies[:6]
    assessment_context["omitted_competencies"] = max(
        0,
        len(assessment.get("competencies", [])) - 6,
    )

    return {
        "focus": (
            "learning_resources"
            if include_resources
            else "career_guidance"
        ),
        "assessment": assessment_context,
        "account": account_context,
    }

def is_cv_ranking_question(message: str) -> bool:
    terms = (
        "random forest",
        "rf score",
        "model score",
        "documented coverage",
        "skill coverage",
        "cv analysis",
        "career recommendation",
        "recommended careers",
        "career ranking",
    )
    return any(term in message.lower() for term in terms)

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

    context = build_grounded_mentor_context(
        db=db,
        user_id=user_id,
        career_key=career_key,
        assessment=assessment,
        include_resources=is_learning_resource_question(message),
        message=message,
    )

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
    pre_saved_user_message_id: int | None = None,
) -> dict:

    career_id = db.scalar(
        select(Career.id).where(
            Career.career_key == career_key
        )
    )

    if career_id is None:
        raise ValueError("Career not found.")

    history = []

    # Restore the correct conversation history.
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
        if pre_saved_user_message_id is not None:
            if (
                not history
                or history[-1]["role"] != "user"
                or history[-1]["content"] != message
            ):
                raise ValueError(
                    "Queued message history is inconsistent."
                )

            history = history[:-1]

    # Step 1: Generate competency assessment.
    assessment_started = perf_counter()

    assessment = analyze_competency_gaps(
        db=db,
        user_id=user_id,
        career_key=career_key,
    )

    assessment_seconds = perf_counter() - assessment_started

    # Step 2: Build question-specific context.
    context_started = perf_counter()

    resource_question = should_include_learning_resources(
        message=message,
        history=history,
    )

    context = build_grounded_mentor_context(
        db=db,
        user_id=user_id,
        career_key=career_key,
        assessment=assessment,
        include_resources=resource_question,
        message=message,
    )

    context_seconds = perf_counter() - context_started

    # Step 3: Send the conversation to Ollama.
    llm_started = perf_counter()

    response = await generate_mentor_response(
        message=message,
        context=context,
        history=history,
    )

    llm_seconds = perf_counter() - llm_started

    logger.info(
        "CareerForge Mentor | assessment=%.2fs | "
        "context=%.2fs | ollama=%.2fs | resources=%s",
        assessment_seconds,
        context_seconds,
        llm_seconds,
        resource_question,
    )

    # Step 4: Create a conversation if necessary.
    if conversation_id is None:
        conversation = create_mentor_conversation(
            db=db,
            user_id=user_id,
            career_id=career_id,
            title=make_mentor_title(message),
        )

        conversation_id = conversation.id

    # Step 5: Persist both messages.
    if pre_saved_user_message_id is None:
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
