
"""Add user competency assessments table.

Revision ID: c5a1e8f04b21
Revises: 3f5e527a8003
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5a1e8f04b21"

down_revision: Union[str, None] = "3f5e527a8003"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_competency_assessments",

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
            "career_id",
            sa.Integer(),
            sa.ForeignKey(
                "careers.id",
                ondelete="CASCADE",
            ),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "competency_key",
            sa.String(length=100),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "proficiency_level",
            sa.String(length=20),
            nullable=False,
        ),

        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.CheckConstraint(
            "proficiency_level IN "
            "('beginner', 'intermediate', 'advanced')",
            name="ck_competency_assessment_level",
        ),
    )


def downgrade() -> None:
    op.drop_table("user_competency_assessments")
