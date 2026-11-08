
from sqlalchemy import select

from src.backend.app.database.session import SessionLocal
from src.backend.app.database.models.career import Career
from src.backend.app.database.models.mentor import (
    MentorConversation,
    MentorMessage,
)
from src.backend.app.services.mentor_conversation_service import (
    make_mentor_title,
)


def main():
    updated = 0

    with SessionLocal() as db:
        conversations = db.scalars(
            select(MentorConversation)
        ).all()

        for conversation in conversations:
            if conversation.career_id is None:
                continue

            career = db.get(Career, conversation.career_id)

            if career is None:
                continue

            if conversation.title != f"{career.name} Assessment":
                continue

            first_message = db.scalar(
                select(MentorMessage.content)
                .where(
                    MentorMessage.conversation_id == conversation.id,
                    MentorMessage.role == "user",
                )
                .order_by(MentorMessage.id)
                .limit(1)
            )

            if not first_message:
                continue

            conversation.title = make_mentor_title(first_message)
            updated += 1

        db.commit()

    print(f"Updated {updated} conversation titles.")


if __name__ == "__main__":
    main()
