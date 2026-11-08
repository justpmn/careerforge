"""restore authentication support tables

Revision ID: 9cb5edaf78cf
Revises: acddd6f4ed57
Create Date: 2026-11-07 12:48:18.498198

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9cb5edaf78cf'
down_revision: Union[str, Sequence[str], None] = 'acddd6f4ed57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
