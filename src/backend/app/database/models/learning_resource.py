
from sqlalchemy import Index, String, Text, DateTime
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.app.database.base import Base


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(150), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
    )


Index(
    "uq_learning_resources_url",
    LearningResource.url,
    unique=True,
)
