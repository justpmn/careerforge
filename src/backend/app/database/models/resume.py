from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.app.database.base import Base
from sqlalchemy.dialects.postgresql import JSONB

class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    file_name: Mapped[str] = mapped_column(String(255),nullable=False)
    file_type: Mapped[str] = mapped_column(String(20),nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    analysis_result: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True,
)