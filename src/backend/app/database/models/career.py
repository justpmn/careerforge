from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.app.database.base import Base


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    career_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        index=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    responsibilities: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    education_requirements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )