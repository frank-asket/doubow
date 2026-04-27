"""add job provider ingestion run/source tables

Revision ID: 20260501_00
Revises: 20260430_00
Create Date: 2026-05-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260501_00"
down_revision = "20260430_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_ingestion_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'running'")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_seen", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_upserted", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_ingestion_runs_provider", "job_ingestion_runs", ["provider"], unique=False)

    op.create_table(
        "job_source_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_job_id", sa.String(length=255), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_job_id", name="uq_job_source_records_provider_job"),
    )
    op.create_index("ix_job_source_records_provider", "job_source_records", ["provider"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_source_records_provider", table_name="job_source_records")
    op.drop_table("job_source_records")
    op.drop_index("ix_job_ingestion_runs_provider", table_name="job_ingestion_runs")
    op.drop_table("job_ingestion_runs")
