"""enforce normalized user email uniqueness

Revision ID: 9473bc466676
Revises: 3f4d9e620855
Create Date: 2026-10-25 19:44:27.397515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9473bc466676'
down_revision: Union[str, Sequence[str], None] = '3f4d9e620855'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_index(
        "uq_users_email_normalized",
        "users",
        [sa.text("lower(btrim(email))")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_users_email_normalized",
        table_name="users",
    )
