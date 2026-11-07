"""restore user learning progress table

Revision ID: acddd6f4ed57
Revises: b19dbcdd49a3
Create Date: 2026-11-07 11:44:44.262283

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acddd6f4ed57'
down_revision: Union[str, Sequence[str], None] = 'b19dbcdd49a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if not sa.inspect(op.get_bind()).has_table(
        "user_learning_progress"
    ):
        op.create_table(
            "oauth_identities",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(20), nullable=False),
            sa.Column("provider_user_id", sa.String(255), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"], ["users.id"],
                name="oauth_identities_user_id_fkey",
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint(
                "provider", "provider_user_id",
                name="uq_oauth_provider_identity",
            ),
        )

    if sa.inspect(bind).has_table("oauth_identities"):
        indexes = {
            item["name"]
            for item in sa.inspect(bind).get_indexes("oauth_identities")
        }
        if "ix_oauth_identities_user_id" not in indexes:
            op.create_index(
                "ix_oauth_identities_user_id",
                "oauth_identities",
                ["user_id"],
            )

    if not sa.inspect(bind).has_table("password_reset_tokens"):
        op.create_table(
            "password_reset_tokens",
            sa.Column("user_id", sa.Integer(), primary_key=True),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "expires_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"], ["users.id"],
                name="password_reset_tokens_user_id_fkey",
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint(
                "token_hash",
                name="password_reset_tokens_token_hash_key",
            ),
        )

    if not sa.inspect(bind).has_table("account_deletion_tokens"):
        op.create_table(
            "account_deletion_tokens",
            sa.Column(
                "id",
                sa.Integer(),
                sa.Identity(),
                primary_key=True,
            ),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(64), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "expires_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"], ["users.id"],
                name="account_deletion_tokens_user_id_fkey",
                ondelete="CASCADE",
            ),
            sa.UniqueConstraint(
                "user_id", name="uq_deletion_token_user"
            ),
            sa.UniqueConstraint(
                "token_hash", name="uq_deletion_token_hash"
            ),
        )


def downgrade() -> None:
    raise RuntimeError(
        "Manual downgrade required: these security tables may "
        "contain existing user data and must not be dropped automatically."
    )
