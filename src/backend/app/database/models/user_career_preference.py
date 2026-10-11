from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.app.database.base import Base


class UserCareerPreference(Base):
    __tablename__ = "user_career_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    career_id: Mapped[int] = mapped_column(
        ForeignKey(
            "careers.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    preference: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )