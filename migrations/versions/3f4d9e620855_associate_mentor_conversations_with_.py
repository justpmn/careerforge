"""associate mentor conversations with careers

Revision ID: 3f4d9e620855
Revises: 9937c669162d
Create Date: 2026-10-24 20:31:01.961166

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3f4d9e620855"
down_revision: Union[str, Sequence[str], None] = "9937c669162d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mentor_conversations",
        sa.Column(
            "career_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_mentor_conversations_career_id",
        "mentor_conversations",
        ["career_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_mentor_conversations_career_id",
        "mentor_conversations",
        "careers",
        ["career_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_mentor_conversations_career_id",
        "mentor_conversations",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_mentor_conversations_career_id",
        table_name="mentor_conversations",
    )

    op.drop_column(
        "mentor_conversations",
        "career_id",
    )
