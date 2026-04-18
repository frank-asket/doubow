"""widen Clerk user ids; scope idempotency keys per user

Revision ID: 20260418_01
Revises: 20260417_02
Create Date: 2026-04-18
"""

import sqlalchemy as sa
from alembic import op

revision = "20260418_01"
down_revision = "20260417_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_autopilot_runs_idempotency_key", "autopilot_runs", type_="unique")
    op.drop_constraint("uq_applications_idempotency_key", "applications", type_="unique")
    op.drop_constraint("uq_approvals_idempotency_key", "approvals", type_="unique")

    for table in ("resumes", "applications", "approvals", "autopilot_runs", "prep_sessions", "job_scores"):
        op.alter_column(
            table,
            "user_id",
            type_=sa.String(length=128),
            existing_type=sa.String(length=36),
            existing_nullable=False,
        )

    op.alter_column(
        "users",
        "id",
        type_=sa.String(length=128),
        existing_type=sa.String(length=36),
        existing_nullable=False,
    )

    op.create_unique_constraint(
        "uq_autopilot_runs_user_idempotency",
        "autopilot_runs",
        ["user_id", "idempotency_key"],
    )
    op.create_unique_constraint(
        "uq_applications_user_idempotency",
        "applications",
        ["user_id", "idempotency_key"],
    )
    op.create_unique_constraint(
        "uq_approvals_user_idempotency",
        "approvals",
        ["user_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_approvals_user_idempotency", "approvals", type_="unique")
    op.drop_constraint("uq_applications_user_idempotency", "applications", type_="unique")
    op.drop_constraint("uq_autopilot_runs_user_idempotency", "autopilot_runs", type_="unique")

    op.create_unique_constraint("uq_approvals_idempotency_key", "approvals", ["idempotency_key"])
    op.create_unique_constraint("uq_applications_idempotency_key", "applications", ["idempotency_key"])
    op.create_unique_constraint("uq_autopilot_runs_idempotency_key", "autopilot_runs", ["idempotency_key"])

    op.alter_column(
        "users",
        "id",
        type_=sa.String(length=36),
        existing_type=sa.String(length=128),
        existing_nullable=False,
    )

    for table in ("job_scores", "prep_sessions", "autopilot_runs", "approvals", "applications", "resumes"):
        op.alter_column(
            table,
            "user_id",
            type_=sa.String(length=36),
            existing_type=sa.String(length=128),
            existing_nullable=False,
        )
