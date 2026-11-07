
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.app.database.base import Base


class CompetencyResourceLink(Base):
    __tablename__ = "competency_resource_links"

    career_key: Mapped[str] = mapped_column(
        String(120),
        primary_key=True,
    )

    competency_key: Mapped[str] = mapped_column(
        String(120),
        primary_key=True,
    )

    resource_id: Mapped[int] = mapped_column(
        ForeignKey("learning_resources.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
