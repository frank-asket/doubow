"""add job provider ingestion run/source tables

Revision ID: 20260501_00
Revises: 20260430_00
Create Date: 2026-05-01 00:00:00.000000
"""

from alembic import op


revision = "20260501_00"
down_revision = "20260430_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS job_ingestion_runs (
            id VARCHAR(36) PRIMARY KEY,
            provider VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'running',
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ NULL,
            records_seen INTEGER NOT NULL DEFAULT 0,
            records_upserted INTEGER NOT NULL DEFAULT 0,
            error_message TEXT NULL,
            metadata_json JSON NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_job_ingestion_runs_provider ON job_ingestion_runs (provider)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS job_source_records (
            id VARCHAR(36) PRIMARY KEY,
            provider VARCHAR(64) NOT NULL,
            provider_job_id VARCHAR(255) NOT NULL,
            raw_payload JSON NOT NULL,
            fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_job_source_records_provider_job UNIQUE (provider, provider_job_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_job_source_records_provider ON job_source_records (provider)")


def downgrade() -> None:
    op.drop_index("ix_job_source_records_provider", table_name="job_source_records")
    op.drop_table("job_source_records")
    op.drop_index("ix_job_ingestion_runs_provider", table_name="job_ingestion_runs")
    op.drop_table("job_ingestion_runs")
