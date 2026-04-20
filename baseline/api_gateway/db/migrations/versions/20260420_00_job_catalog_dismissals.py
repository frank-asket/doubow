"""catalog jobs + job_dismissals for Discover

Revision ID: 20260420_00
Revises: 20260419_00
Create Date: 2026-04-20
"""

import sqlalchemy as sa
from alembic import op

revision = "20260420_00"
down_revision = "20260419_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_dismissals",
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "job_id"),
    )

    # Curated catalog (source=catalog). Per-user scores are created at runtime in jobs_service.
    op.execute(
        sa.text(
            """
            INSERT INTO jobs (id, source, external_id, title, company, location, salary_range, description, url)
            VALUES
              (
                'jb_cat_001', 'catalog', 'cat-001',
                'Senior AI Product Engineer',
                'Northwind Labs',
                'Remote · EU',
                '€130k–€160k',
                'Own evaluation harnesses, agent workflows, and product metrics for AI features.',
                'https://example.com/jobs/jb_cat_001'
              ),
              (
                'jb_cat_002', 'catalog', 'cat-002',
                'ML Platform Engineer',
                'Riverstone',
                'Berlin / Hybrid',
                '€115k–€140k',
                'Batch inference, feature stores, and reliability for production model serving.',
                'https://example.com/jobs/jb_cat_002'
              ),
              (
                'jb_cat_003', 'catalog', 'cat-003',
                'Staff Backend Engineer',
                'Cobalt Health',
                'Remote · US',
                '$180k–$210k',
                'APIs, data pipelines, and integrations for clinical operations platforms.',
                'https://example.com/jobs/jb_cat_003'
              ),
              (
                'jb_cat_004', 'catalog', 'cat-004',
                'Data Scientist — Growth',
                'Lumen Apps',
                'London',
                '£90k–£110k',
                'Experimentation, causal inference, and forecasting for subscription growth.',
                'https://example.com/jobs/jb_cat_004'
              )
            ON CONFLICT (source, external_id) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM jobs WHERE source = 'catalog'"))
    op.drop_table("job_dismissals")
