
"""Add resource audit history and URL uniqueness."""

from alembic import op
import sqlalchemy as sa


revision = "a6348c71e2bd"
down_revision = "f4c92bd7186e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_learning_resources_url",
        "learning_resources",
        ["url"],
        unique=True,
    )

    op.create_table(
        "admin_resource_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "actor_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("admin_resource_audit")
    op.drop_index(
        "uq_learning_resources_url",
        table_name="learning_resources",
    )
