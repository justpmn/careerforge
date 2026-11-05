"""add user appearance preferences

Revision ID: 1b96e4aca67f
Revises: b82f6c5a104d
Create Date: 2026-11-05 08:53:20.409341

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b96e4aca67f'
down_revision: Union[str, Sequence[str], None] = 'b82f6c5a104d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "appearance",
            sa.String(length=10),
            server_default="cozy",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "cozy_theme",
            sa.String(length=5),
            server_default="light",
            nullable=False,
        ),
    )

    op.create_check_constraint(
        "ck_users_appearance",
        "users",
        "appearance IN ('cozy', 'neon')",
    )
    op.create_check_constraint(
        "ck_users_cozy_theme",
        "users",
        "cozy_theme IN ('light', 'dark')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_users_cozy_theme", "users", type_="check"
    )
    op.drop_constraint(
        "ck_users_appearance", "users", type_="check"
    )
    op.drop_column("users", "cozy_theme")
    op.drop_column("users", "appearance")

