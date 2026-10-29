from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.app.database.base import Base


class UserLearningProgress(Base):
    __tablename__ = "user_learning_progress"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    career_id: Mapped[int] = mapped_column(
        ForeignKey("careers.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    learned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
