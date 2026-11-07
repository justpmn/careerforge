
from datetime import datetime

from sqlalchemy import (
    DateTime, ForeignKey, Identity, Integer,
    String, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.app.database.base import Base


class AccountDeletionToken(Base):
    __tablename__ = "account_deletion_tokens"

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_deletion_token_user"),
        UniqueConstraint("token_hash", name="uq_deletion_token_hash"),
    )

    id: Mapped[int] = mapped_column(
        Integer, Identity(), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
