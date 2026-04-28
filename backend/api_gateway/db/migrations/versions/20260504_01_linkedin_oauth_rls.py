"""RLS for linkedin_oauth_credentials

Revision ID: 20260504_01
Revises: 20260504_00
Create Date: 2026-05-04
"""

from alembic import op

revision = "20260504_01"
down_revision = "20260504_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(
        """
        ALTER TABLE linkedin_oauth_credentials ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS doubow_linkedin_oauth_credentials_tenant ON linkedin_oauth_credentials;
        CREATE POLICY doubow_linkedin_oauth_credentials_tenant ON linkedin_oauth_credentials
          FOR ALL
          USING (user_id = public.doubow_current_user_id())
          WITH CHECK (user_id = public.doubow_current_user_id());
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP POLICY IF EXISTS doubow_linkedin_oauth_credentials_tenant ON linkedin_oauth_credentials;")
    op.execute("ALTER TABLE linkedin_oauth_credentials DISABLE ROW LEVEL SECURITY;")

