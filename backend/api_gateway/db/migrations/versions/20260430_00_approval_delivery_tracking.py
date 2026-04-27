"""Track provider delivery confirmation metadata for approvals.

Revision ID: 20260430_00
Revises: 20260429_00
Create Date: 2026-04-30
"""

from alembic import op

revision = "20260430_00"
down_revision = "20260429_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent DDL: these columns may already exist on long-lived environments
    # where startup guards added them before this revision was applied.
    op.execute("ALTER TABLE approvals ADD COLUMN IF NOT EXISTS send_provider VARCHAR(32)")
    op.execute(
        "ALTER TABLE approvals ADD COLUMN IF NOT EXISTS delivery_status VARCHAR(32) NOT NULL DEFAULT 'not_sent'"
    )
    op.execute("ALTER TABLE approvals ADD COLUMN IF NOT EXISTS delivery_error TEXT")
    op.execute("ALTER TABLE approvals ADD COLUMN IF NOT EXISTS provider_message_id VARCHAR(255)")
    op.execute("ALTER TABLE approvals ADD COLUMN IF NOT EXISTS provider_thread_id VARCHAR(255)")
    op.execute("ALTER TABLE approvals ADD COLUMN IF NOT EXISTS provider_confirmed_at TIMESTAMPTZ")

    op.execute(
        """
        UPDATE approvals
        SET delivery_status = CASE
            WHEN sent_at IS NOT NULL THEN 'provider_accepted'
            WHEN approved_at IS NOT NULL THEN 'queued'
            ELSE 'not_sent'
        END
        """
    )
    op.alter_column("approvals", "delivery_status", server_default=None)


def downgrade() -> None:
    op.drop_column("approvals", "provider_confirmed_at")
    op.drop_column("approvals", "provider_thread_id")
    op.drop_column("approvals", "provider_message_id")
    op.drop_column("approvals", "delivery_error")
    op.drop_column("approvals", "delivery_status")
    op.drop_column("approvals", "send_provider")
