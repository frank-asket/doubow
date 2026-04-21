"""normalize foreign-key index naming consistency

Revision ID: 20260417_02
Revises: 20260417_01
Create Date: 2026-04-17
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260417_02"
down_revision = "20260417_01"
branch_labels = None
depends_on = None


def _create_index_if_missing(index_name: str, table_name: str, column_name: str) -> None:
    op.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})")


def _drop_index_if_exists(index_name: str) -> None:
    op.execute(f"DROP INDEX IF EXISTS {index_name}")


def upgrade() -> None:
    # users
    _create_index_if_missing("ix_users_email", "users", "email")

    # resumes
    _create_index_if_missing("ix_resumes_user_id", "resumes", "user_id")

    # jobs
    _create_index_if_missing("ix_jobs_source", "jobs", "source")

    # job_scores
    _create_index_if_missing("ix_job_scores_user_id", "job_scores", "user_id")
    _create_index_if_missing("ix_job_scores_job_id", "job_scores", "job_id")

    # applications
    _create_index_if_missing("ix_applications_user_id", "applications", "user_id")
    _create_index_if_missing("ix_applications_job_id", "applications", "job_id")

    # approvals
    _create_index_if_missing("ix_approvals_user_id", "approvals", "user_id")
    _create_index_if_missing("ix_approvals_application_id", "approvals", "application_id")

    # autopilot_runs
    _create_index_if_missing("ix_autopilot_runs_user_id", "autopilot_runs", "user_id")

    # prep_sessions
    _create_index_if_missing("ix_prep_sessions_user_id", "prep_sessions", "user_id")
    _create_index_if_missing("ix_prep_sessions_application_id", "prep_sessions", "application_id")


def downgrade() -> None:
    _drop_index_if_exists("ix_prep_sessions_application_id")
    _drop_index_if_exists("ix_prep_sessions_user_id")
    _drop_index_if_exists("ix_autopilot_runs_user_id")
    _drop_index_if_exists("ix_approvals_application_id")
    _drop_index_if_exists("ix_approvals_user_id")
    _drop_index_if_exists("ix_applications_job_id")
    _drop_index_if_exists("ix_applications_user_id")
    _drop_index_if_exists("ix_job_scores_job_id")
    _drop_index_if_exists("ix_job_scores_user_id")
    _drop_index_if_exists("ix_jobs_source")
    _drop_index_if_exists("ix_resumes_user_id")
    _drop_index_if_exists("ix_users_email")
