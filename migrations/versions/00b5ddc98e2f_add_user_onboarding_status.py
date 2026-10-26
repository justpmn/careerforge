"""add user onboarding status

Revision ID: 00b5ddc98e2f
Revises: 9473bc466676
Create Date: 2026-10-26 16:26:19.014227

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00b5ddc98e2f'
down_revision: Union[str, Sequence[str], None] = '9473bc466676'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed")
