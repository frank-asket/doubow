"""add job_scores table

Revision ID: 20260417_01
Revises:
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260417_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_scores",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("fit_score", sa.Numeric(3, 1), nullable=False),
        sa.Column("fit_reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("risk_flags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("dimension_scores", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id", name="uq_job_scores_user_job"),
    )
    op.create_index(op.f("ix_job_scores_user_id"), "job_scores", ["user_id"], unique=False)
    op.create_index(op.f("ix_job_scores_job_id"), "job_scores", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_scores_job_id"), table_name="job_scores")
    op.drop_index(op.f("ix_job_scores_user_id"), table_name="job_scores")
    op.drop_table("job_scores")
