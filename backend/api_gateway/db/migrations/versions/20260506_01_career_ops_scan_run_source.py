"""Add source column to career ops scan runs.

Revision ID: 20260506_01
Revises: 20260506_00
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260506_01"
down_revision = "20260506_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("career_ops_scan_runs", sa.Column("source", sa.String(length=64), nullable=True))
    op.create_index("ix_career_ops_scan_runs_source", "career_ops_scan_runs", ["source"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_career_ops_scan_runs_source", table_name="career_ops_scan_runs")
    op.drop_column("career_ops_scan_runs", "source")
