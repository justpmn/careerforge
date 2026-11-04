
"""Add competency-resource mappings.

Revision ID: f4c92bd7186e
Revises: e2b84f7c1930
"""

from alembic import op
import sqlalchemy as sa


revision = "f4c92bd7186e"
down_revision = "e2b84f7c1930"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "competency_resource_links",
        sa.Column(
            "career_key",
            sa.String(120),
            primary_key=True,
        ),
        sa.Column(
            "competency_key",
            sa.String(120),
            primary_key=True,
        ),
        sa.Column(
            "resource_id",
            sa.Integer(),
            sa.ForeignKey(
                "learning_resources.id",
                ondelete="CASCADE",
            ),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_competency_resource_links_resource_id",
        "competency_resource_links",
        ["resource_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_competency_resource_links_resource_id",
        table_name="competency_resource_links",
    )
    op.drop_table("competency_resource_links")
