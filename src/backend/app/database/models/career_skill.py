from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.app.database.base import Base

class CareerSkill(Base):
    __tablename__ = "career_skills"
    career_id: Mapped[int] = mapped_column(
        ForeignKey("careers.id", ondelete="CASCADE"),
        primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True
    )
    importance_level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )