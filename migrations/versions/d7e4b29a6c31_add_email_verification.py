
"""Add email verification support.

Revision ID: d7e4b29a6c31
Revises: c5a1e8f04b21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7e4b29a6c31"
down_revision: Union[str, None] = "c5a1e8f04b21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "email_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Grandfather existing users to avoid locking out
    # accounts created before email verification.
    op.execute(
        "UPDATE users SET email_verified_at = NOW() "
        "WHERE email_verified_at IS NULL"
    )

    op.create_table(
        "email_verification_tokens",

        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "token_hash",
            name="uq_email_verification_tokens_hash",
        ),
    )


def downgrade() -> None:
    op.drop_table("email_verification_tokens")
    op.drop_column("users", "email_verified_at")
