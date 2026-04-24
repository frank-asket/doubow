"""Store LangGraph autopilot checkpoint JSON for resume across worker restarts.

Revision ID: 20260429_00
Revises: 20260428_00
Create Date: 2026-04-23
"""

import sqlalchemy as sa
from alembic import op

revision = "20260429_00"
down_revision = "20260428_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("autopilot_runs", sa.Column("graph_checkpoint", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("autopilot_runs", "graph_checkpoint")
