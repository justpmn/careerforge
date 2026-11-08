
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.backend.app.database.models.mentor import (MentorConversation,MentorMessage,)
from src.backend.app.database.models.career import Career


def create_mentor_conversation(
    db: Session,
    user_id: int,
    title: str | None = None,
    career_id: int | None = None,
) -> MentorConversation:

    if title is not None:
        title = title.strip()

        if len(title) > 255:
            raise ValueError("Conversation title is too long.")

    conversation = MentorConversation(
        user_id=user_id,
        career_id=career_id,
        title=title or None,
    )

    db.add(conversation)
    db.flush()

    return conversation

def get_owned_conversation(
    db: Session,
    user_id: int,
    conversation_id: int,
) -> MentorConversation:

    conversation = db.scalar(
        select(MentorConversation).where(
            MentorConversation.id == conversation_id,
            MentorConversation.user_id == user_id,
        )
    )

    if conversation is None:
        raise ValueError("Conversation not found.")

    return conversation

def save_mentor_message(
    db: Session,
    user_id: int,
    conversation_id: int,
    role: str,
    content: str,
) -> MentorMessage:

    conversation = get_owned_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    if role not in {"user", "assistant"}:
        raise ValueError("Invalid message role.")

    if not isinstance(content, str) or not content.strip():
        raise ValueError("Message content cannot be empty.")

    database_role = (
        "mentor" if role == "assistant" else "user"
    )

    message = MentorMessage(
        conversation_id=conversation.id,
        role=database_role,
        content=content.strip(),
    )

    db.add(message)

    conversation.updated_at = datetime.now(timezone.utc)

    db.flush()

    return message

def get_recent_mentor_history(
    db: Session,
    user_id: int,
    conversation_id: int,
    limit: int = 6,
) -> list[dict[str, str]]:

    get_owned_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    if not 1 <= limit <= 6:
        raise ValueError("History limit must be between 1 and 6.")

    messages = db.scalars(
        select(MentorMessage)
        .where(
            MentorMessage.conversation_id == conversation_id,
        )
        .order_by(
            MentorMessage.created_at.desc(),
            MentorMessage.id.desc(),
        )
        .limit(limit)
    ).all()

    return [
        {
            "role": (
                "assistant"
                if message.role == "mentor"
                else "user"
            ),
            "content": message.content,
        }
        for message in reversed(messages)
    ]


def list_owned_mentor_conversations(
    db: Session,
    user_id: int,
    limit: int = 50,
) -> list[MentorConversation]:

    if not 1 <= limit <= 50:
        raise ValueError("Invalid conversation limit.")

    return list(
        db.scalars(
            select(MentorConversation)
            .where(MentorConversation.user_id == user_id)
            .order_by(
                MentorConversation.updated_at.desc(),
                MentorConversation.id.desc(),
            )
            .limit(limit)
        ).all()
    )


def list_owned_mentor_messages(
    db: Session,
    user_id: int,
    conversation_id: int,
    limit: int = 50,
) -> list[dict]:

    get_owned_conversation(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    if not 1 <= limit <= 50:
        raise ValueError("Invalid message limit.")

    messages = db.scalars(
        select(MentorMessage)
        .where(
            MentorMessage.conversation_id == conversation_id
        )
        .order_by(MentorMessage.id.desc())
        .limit(limit)
    ).all()

    return [
        {
            "id": item.id,
            "role": (
                "assistant"
                if item.role == "mentor"
                else "user"
            ),
            "content": item.content,
            "created_at": item.created_at,
        }
        for item in reversed(messages)
    ]


def make_mentor_title(message: str, max_length: int = 60) -> str:
    title = " ".join(message.split())

    if not title:
        return "New conversation"

    if len(title) <= max_length:
        return title

    shortened = title[:max_length - 1].rsplit(" ", 1)[0]
    return (shortened or title[:max_length - 1]).rstrip(".,:;!? ") + "…"