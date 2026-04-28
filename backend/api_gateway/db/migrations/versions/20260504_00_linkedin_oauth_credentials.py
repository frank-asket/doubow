"""LinkedIn OAuth credentials table

Revision ID: 20260504_00
Revises: 20260503_00
Create Date: 2026-05-04
"""

import sqlalchemy as sa
from alembic import op

revision = "20260504_00"
down_revision = "20260503_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS linkedin_oauth_credentials (
            user_id VARCHAR(128) NOT NULL PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            access_token_encrypted TEXT NOT NULL,
            linkedin_member_id VARCHAR(255),
            expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_linkedin_oauth_credentials_linkedin_member_id "
        "ON linkedin_oauth_credentials (linkedin_member_id);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_linkedin_oauth_credentials_linkedin_member_id;")
    op.execute("DROP TABLE IF EXISTS linkedin_oauth_credentials;")

