"""Row Level Security — tenant isolation via session GUC app.current_user_id

Revision ID: 20260422_00
Revises: 20260421_00
Create Date: 2026-04-22

The API sets app.current_user_id per transaction (see db/session.py). Policies enforce
user-scoped rows. Connections as PostgreSQL superuser bypass RLS; use a non-superuser
role for the app in production so policies apply.
"""

from alembic import op

revision = "20260422_00"
down_revision = "20260421_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute(
        """
        CREATE OR REPLACE FUNCTION public.doubow_current_user_id()
        RETURNS text
        LANGUAGE sql
        STABLE
        AS $$
          SELECT NULLIF(btrim(COALESCE(current_setting('app.current_user_id', true), '')), '')
        $$;
        """
    )

    # Shared job catalog: readable/writable by API role (discovery + manual job rows).
    op.execute(
        """
        ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS doubow_jobs_rw ON jobs;
        CREATE POLICY doubow_jobs_rw ON jobs FOR ALL USING (true) WITH CHECK (true);
        """
    )

    # users.id is the tenant key (no user_id column)
    op.execute(
        """
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;
        DROP POLICY IF EXISTS doubow_users_tenant ON users;
        CREATE POLICY doubow_users_tenant ON users
          FOR ALL
          USING (id = public.doubow_current_user_id())
          WITH CHECK (id = public.doubow_current_user_id());
        """
    )

    for table in (
        "resumes",
        "applications",
        "approvals",
        "prep_sessions",
        "job_scores",
        "job_dismissals",
        "autopilot_runs",
    ):
        op.execute(
            f"""
            ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS doubow_{table}_tenant ON {table};
            CREATE POLICY doubow_{table}_tenant ON {table}
              FOR ALL
              USING (user_id = public.doubow_current_user_id())
              WITH CHECK (user_id = public.doubow_current_user_id());
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP POLICY IF EXISTS doubow_jobs_rw ON jobs;")
    op.execute("ALTER TABLE jobs DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS doubow_users_tenant ON users;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")

    for table in (
        "resumes",
        "applications",
        "approvals",
        "prep_sessions",
        "job_scores",
        "job_dismissals",
        "autopilot_runs",
    ):
        op.execute(f"DROP POLICY IF EXISTS doubow_{table}_tenant ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP FUNCTION IF EXISTS public.doubow_current_user_id();")
