"""backfill greenhouse logo host to canonical boards domain

Revision ID: 20260501_01
Revises: 20260501_00
Create Date: 2026-05-01 00:30:00.000000
"""

from alembic import op


revision = "20260501_01"
down_revision = "20260501_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE jobs
        SET logo_url = replace(logo_url, 'logo.clearbit.com/job-boards.greenhouse.io', 'logo.clearbit.com/boards.greenhouse.io')
        WHERE logo_url LIKE 'https://logo.clearbit.com/job-boards.greenhouse.io%';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE jobs
        SET logo_url = replace(logo_url, 'logo.clearbit.com/boards.greenhouse.io', 'logo.clearbit.com/job-boards.greenhouse.io')
        WHERE logo_url LIKE 'https://logo.clearbit.com/boards.greenhouse.io%';
        """
    )
