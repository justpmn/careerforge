"""add user target career

Revision ID: 8a5c65e70655
Revises: 44d09b302c6a
Create Date: 2026-10-26 20:45:27.966435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a5c65e70655'
down_revision: Union[str, Sequence[str], None] = '44d09b302c6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "target_career_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_users_target_career",
        "users",
        "careers",
        ["target_career_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_users_target_career",
        "users",
        type_="foreignkey",
    )

    op.drop_column(
        "users",
        "target_career_id",
    )