"""add file_name to resumes

Revision ID: 20260419_00
Revises: 20260418_01
Create Date: 2026-04-19
"""

import sqlalchemy as sa
from alembic import op

revision = "20260419_00"
down_revision = "20260418_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resumes",
        sa.Column("file_name", sa.String(length=255), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("resumes", "file_name")
