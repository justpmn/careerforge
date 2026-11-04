
"""Add administrator MFA credentials and recovery codes.

Revision ID: e2b84f7c1930
Revises: d7e4b29a6c31
"""

from alembic import op
import sqlalchemy as sa


revision = "e2b84f7c1930"
down_revision = "d7e4b29a6c31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_mfa_credentials",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("pending_secret_encrypted", sa.Text()),
        sa.Column(
            "pending_expires_at",
            sa.DateTime(timezone=True),
        ),
        sa.Column("totp_secret_encrypted", sa.Text()),
        sa.Column(
            "enabled_at",
            sa.DateTime(timezone=True),
        ),
        sa.Column("last_accepted_step", sa.BigInteger()),
        sa.Column(
            "failed_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "locked_until",
            sa.DateTime(timezone=True),
        ),
        sa.Column(
            "mfa_version",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "admin_mfa_recovery_codes",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "code_hash",
            sa.String(64),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_admin_mfa_recovery_codes_user_id",
        "admin_mfa_recovery_codes",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_admin_mfa_recovery_codes_user_id",
        table_name="admin_mfa_recovery_codes",
    )
    op.drop_table("admin_mfa_recovery_codes")
    op.drop_table("admin_mfa_credentials")
