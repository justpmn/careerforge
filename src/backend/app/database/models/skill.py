from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.app.database.base import Base

class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )
    category: Mapped[str | None] = mapped_column(String(100),nullable=True)
    description: Mapped[str | None] = mapped_column(Text,nullable=True)