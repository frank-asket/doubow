"""Google OAuth credentials for Gmail API send

Revision ID: 20260423_00
Revises: 20260422_00
Create Date: 2026-04-23
"""

import sqlalchemy as sa
from alembic import op

revision = "20260423_00"
down_revision = "20260422_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "google_oauth_credentials",
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=False),
        sa.Column("google_email", sa.String(length=255), nullable=True),
        sa.Column(
            "scopes",
            sa.String(length=500),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        "ix_google_oauth_credentials_google_email",
        "google_oauth_credentials",
        ["google_email"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_google_oauth_credentials_google_email", table_name="google_oauth_credentials")
    op.drop_table("google_oauth_credentials")
