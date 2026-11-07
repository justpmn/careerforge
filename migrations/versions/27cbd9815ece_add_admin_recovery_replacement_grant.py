"""add admin recovery replacement grant

Revision ID: 27cbd9815ece
Revises: 7f59b061b456
Create Date: 2026-11-06 23:21:43.431831

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '27cbd9815ece'
down_revision: Union[str, Sequence[str], None] = '7f59b061b456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "admin_mfa_credentials",
        sa.Column("recovery_grant_hash", sa.String(64), nullable=True),
    )
    op.add_column(
        "admin_mfa_credentials",
        sa.Column(
            "recovery_grant_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("admin_mfa_credentials", "recovery_grant_expires_at")
    op.drop_column("admin_mfa_credentials", "recovery_grant_hash")