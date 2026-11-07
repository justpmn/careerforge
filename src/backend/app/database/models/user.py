from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, false, func, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.backend.app.database.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="user",
        nullable=False,
    )

    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=false(),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    target_career_id: Mapped[int | None] = mapped_column(
    ForeignKey("careers.id", ondelete="SET NULL"),
    nullable=True,
    )
    appearance: Mapped[str] = mapped_column(
        String(10),
        default="cozy",
        server_default="cozy",
        nullable=False,
    )

    cozy_theme: Mapped[str] = mapped_column(
        String(5),
        default="light",
        server_default="light",
        nullable=False,
    )
    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    suspension_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    session_version: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )




Index(
    "uq_users_email_normalized",
    func.lower(func.btrim(User.email)),
    unique=True,
)
