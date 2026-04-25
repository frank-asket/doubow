"""add canonical url/logo/raw-clean job description fields

Revision ID: 20260426_01
Revises: 20260426_00
Create Date: 2026-04-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260426_01"
down_revision = "20260426_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("logo_url", sa.String(length=1000), nullable=True))
    op.add_column("jobs", sa.Column("description_raw", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("description_clean", sa.Text(), nullable=True))
    op.add_column("jobs", sa.Column("canonical_url", sa.String(length=1000), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "canonical_url")
    op.drop_column("jobs", "description_clean")
    op.drop_column("jobs", "description_raw")
    op.drop_column("jobs", "logo_url")

