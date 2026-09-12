from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.app.database.base import Base

class LearningResourceSkill(Base):
    __tablename__ = "learning_resource_skills"
    learning_resource_id: Mapped[int] = mapped_column(
        ForeignKey("learning_resources.id", ondelete="CASCADE"),
        primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True
    )