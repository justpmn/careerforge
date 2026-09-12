from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.app.database.base import Base


class SkillGap(Base):
    __tablename__ = "skill_gaps"
    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True
    )
    gap_score: Mapped[float | None] = mapped_column(Float,nullable=True)