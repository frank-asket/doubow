"""Add nullable profile_views on users for dashboard metric.

Revision ID: 20260426_00
Revises: 20260425_00
Create Date: 2026-04-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20260426_00"
down_revision = "20260425_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("profile_views", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "profile_views")
