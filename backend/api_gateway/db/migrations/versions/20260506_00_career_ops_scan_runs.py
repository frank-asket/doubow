"""Add career ops scan run tracking table.

Revision ID: 20260506_00
Revises: 20260504_02
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260506_00"
down_revision = "20260504_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "career_ops_scan_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="queued"),
        sa.Column("query", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("sources_json", sa.JSON(), nullable=True),
        sa.Column("max_results", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("min_fit_threshold", sa.Numeric(3, 1), nullable=False, server_default="0.0"),
        sa.Column("queue_top_n", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deduped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("kept_after_threshold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("queued_to_pipeline", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("source_mix_json", sa.JSON(), nullable=True),
        sa.Column("top_job_ids_json", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_ops_scan_runs_user_id", "career_ops_scan_runs", ["user_id"], unique=False)
    op.create_index("ix_career_ops_scan_runs_status", "career_ops_scan_runs", ["status"], unique=False)
    op.create_index("ix_career_ops_scan_runs_created_at", "career_ops_scan_runs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_career_ops_scan_runs_created_at", table_name="career_ops_scan_runs")
    op.drop_index("ix_career_ops_scan_runs_status", table_name="career_ops_scan_runs")
    op.drop_index("ix_career_ops_scan_runs_user_id", table_name="career_ops_scan_runs")
    op.drop_table("career_ops_scan_runs")
