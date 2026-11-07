
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.backend.app.database.base import Base


class AdminMfaCredential(Base):
    __tablename__ = "admin_mfa_credentials"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    pending_secret_encrypted: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    pending_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    totp_secret_encrypted: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    enabled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    last_accepted_step: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True
    )

    failed_attempts: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    mfa_version: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    recovery_grant_hash: Mapped[str | None] = mapped_column(
    String(64), nullable=True
)
    recovery_grant_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AdminMfaRecoveryCode(Base):
    __tablename__ = "admin_mfa_recovery_codes"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    code_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
