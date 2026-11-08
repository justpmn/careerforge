
"""Add learning resource archival support."""

from alembic import op
import sqlalchemy as sa


revision = "b82f6c5a104d"
down_revision = "a6348c71e2bd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "learning_resources",
        sa.Column(
            "archived_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("learning_resources", "archived_at")
