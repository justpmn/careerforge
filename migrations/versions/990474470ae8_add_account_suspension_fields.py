"""add account suspension fields

Revision ID: 990474470ae8
Revises: 1b96e4aca67f
Create Date: 2026-11-05 10:29:45.745528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '990474470ae8'
down_revision: Union[str, Sequence[str], None] = '1b96e4aca67f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("suspension_reason", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "suspension_reason")
    op.drop_column("users", "suspended_at")
