"""add account deletion tokens

Revision ID: d872e4a3edb8
Revises: 990474470ae8
Create Date: 2026-11-05 11:55:30.030684

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd872e4a3edb8'
down_revision: Union[str, Sequence[str], None] = '990474470ae8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        "account_deletion_tokens",
        sa.Column("id", sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
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
        sa.UniqueConstraint("user_id", name="uq_deletion_token_user"),
        sa.UniqueConstraint("token_hash", name="uq_deletion_token_hash"),
    )


def downgrade() -> None:
    op.drop_table("account_deletion_tokens")

