"""add user learning progress

Revision ID: 3f5e527a8003
Revises: 282d906cab97
Create Date: 2026-10-29 13:58:17.341157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f5e527a8003'
down_revision: Union[str, Sequence[str], None] = '282d906cab97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_learning_progress",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("career_id", sa.Integer(), nullable=False),
        sa.Column("skill_key", sa.String(length=100), nullable=False),
        sa.Column("learned", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["career_id"], ["careers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "career_id", "skill_key"),
    )


def downgrade() -> None:
    op.drop_table("user_learning_progress")