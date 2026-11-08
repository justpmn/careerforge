"""create user competency assessments table

Revision ID: b19dbcdd49a3
Revises: 27cbd9815ece
Create Date: 2026-11-07 09:45:54.885608

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b19dbcdd49a3'
down_revision: Union[str, Sequence[str], None] = '27cbd9815ece'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table(
        "user_learning_progress"
    ):
        op.create_table(
            "user_competency_assessments",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("career_id", sa.Integer(), nullable=False),
            sa.Column(
                "competency_key",
                sa.String(length=100),
                nullable=False,
            ),
            sa.Column(
                "proficiency_level",
                sa.String(length=20),
                nullable=False,
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.CheckConstraint(
                "proficiency_level IN "
                "('beginner', 'intermediate', 'advanced')",
                name="ck_competency_assessment_level",
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
                "competency_key",
            ),
        )


def downgrade() -> None:
    op.drop_table("user_competency_assessments")
