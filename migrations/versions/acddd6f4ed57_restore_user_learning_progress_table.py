"""restore user learning progress table

Revision ID: acddd6f4ed57
Revises: b19dbcdd49a3
Create Date: 2026-11-07 11:44:44.262283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acddd6f4ed57'
down_revision: Union[str, Sequence[str], None] = 'b19dbcdd49a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table(
        "user_learning_progress"
    ):
        return

    op.create_table(
        "user_learning_progress",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("career_id", sa.Integer(), nullable=False),
        sa.Column("skill_key", sa.String(100), nullable=False),
        sa.Column(
            "learned",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["career_id"],
            ["careers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            "career_id",
            "skill_key",
        ),
    )


def downgrade() -> None:
    raise RuntimeError(
        "Manual downgrade required: learning progress "
        "records may contain user data."
    )
