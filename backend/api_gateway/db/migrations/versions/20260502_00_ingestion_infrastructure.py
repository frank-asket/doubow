"""add ingestion infrastructure (runs + job enrichment columns)

Revision ID: 20260502_00
Revises: 20260501_01
Create Date: 2026-05-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260502_00"
down_revision = "20260501_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_runs (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(36) NOT NULL,
            started_at TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ NULL,
            total_fetched INTEGER NOT NULL DEFAULT 0,
            total_inserted INTEGER NOT NULL DEFAULT 0,
            total_dupes INTEGER NOT NULL DEFAULT 0,
            total_errors INTEGER NOT NULL DEFAULT 0,
            results_json TEXT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_ingestion_runs_run_id ON ingestion_runs (run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ingestion_runs_started_at ON ingestion_runs (started_at DESC)")

    conn = op.get_bind()
    for sql in [
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS dedup_hash VARCHAR(32)",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS remote BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_min INTEGER",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS salary_max INTEGER",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS currency VARCHAR(8) NOT NULL DEFAULT 'USD'",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS department TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS employment_type VARCHAR(32) NOT NULL DEFAULT 'full_time'",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS raw_json JSONB NOT NULL DEFAULT '{}'",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true",
    ]:
        conn.execute(sa.text(sql))

    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_dedup_hash ON jobs (dedup_hash)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_is_active ON jobs (is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_discovered_at ON jobs (discovered_at DESC)")

    op.execute(
        """
        UPDATE jobs
        SET dedup_hash = substring(md5(source || ':' || external_id), 1, 32)
        WHERE dedup_hash IS NULL OR dedup_hash = ''
        """
    )


def downgrade() -> None:
    op.drop_index("ix_ingestion_runs_started_at", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_run_id", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")

