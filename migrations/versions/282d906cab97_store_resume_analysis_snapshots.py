"""store resume analysis snapshots

Revision ID: 282d906cab97
Revises: 8a5c65e70655
Create Date: 2026-10-27 10:03:11.355961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '282d906cab97'
down_revision: Union[str, Sequence[str], None] = '8a5c65e70655'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "resumes",
        sa.Column(
            "analysis_result",
            postgresql.JSONB(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("resumes", "analysis_result")