"""Persist structured autopilot run failure metadata.

Revision ID: 20260428_00
Revises: 20260427_00
Create Date: 2026-04-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20260428_00"
down_revision = "20260427_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("autopilot_runs", sa.Column("failure_code", sa.String(length=64), nullable=True))
    op.add_column("autopilot_runs", sa.Column("failure_detail", sa.String(length=500), nullable=True))
    op.add_column("autopilot_runs", sa.Column("failure_node", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("autopilot_runs", "failure_node")
    op.drop_column("autopilot_runs", "failure_detail")
    op.drop_column("autopilot_runs", "failure_code")
