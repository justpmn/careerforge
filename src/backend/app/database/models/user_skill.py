from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.app.database.base import Base


class UserSkill(Base):
    __tablename__ = "user_skills"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True
    )
    source: Mapped[str] = mapped_column(
        String(50),
        default="resume",
        nullable=False
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)