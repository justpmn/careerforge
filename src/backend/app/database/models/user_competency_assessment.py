
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.app.database.base import Base


class UserCompetencyAssessment(Base):
    __tablename__ = "user_competency_assessments"

    __table_args__ = (
        CheckConstraint(
            "proficiency_level IN "
            "('beginner', 'intermediate', 'advanced')",
            name="ck_competency_assessment_level",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    career_id: Mapped[int] = mapped_column(
        ForeignKey("careers.id", ondelete="CASCADE"),
        primary_key=True,
    )

    competency_key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    proficiency_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
