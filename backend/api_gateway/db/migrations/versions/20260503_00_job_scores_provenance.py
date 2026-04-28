"""persist score provenance on job_scores

Revision ID: 20260503_00
Revises: 20260502_00
Create Date: 2026-05-03 00:00:00.000000
"""

from alembic import op


revision = "20260503_00"
down_revision = "20260502_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE job_scores ADD COLUMN IF NOT EXISTS provenance VARCHAR(32)")
    op.execute(
        """
        UPDATE job_scores
        SET provenance = CASE
            WHEN fit_reasons::text ILIKE '%Semantic similarity signal:%'
              OR fit_reasons::text ILIKE '%Keyword overlap signal:%'
              OR fit_reasons::text ILIKE '%LLM fit signal:%' THEN 'computed'
            WHEN fit_reasons::text ILIKE '%Imported via discovery%' THEN 'template_default'
            WHEN fit_reasons::text ILIKE '%Catalog:%'
              OR fit_reasons::text ILIKE '%seed%'
              OR fit_reasons::text ILIKE '%template%' THEN 'template_seeded'
            ELSE 'unknown'
        END
        WHERE provenance IS NULL OR provenance = ''
        """
    )
    op.execute("ALTER TABLE job_scores ALTER COLUMN provenance SET DEFAULT 'unknown'")
    op.execute("UPDATE job_scores SET provenance = 'unknown' WHERE provenance IS NULL OR provenance = ''")
    op.execute("ALTER TABLE job_scores ALTER COLUMN provenance SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE job_scores DROP COLUMN IF EXISTS provenance")
