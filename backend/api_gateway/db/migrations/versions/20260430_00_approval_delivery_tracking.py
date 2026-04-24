"""Track provider delivery confirmation metadata for approvals.

Revision ID: 20260430_00
Revises: 20260429_00
Create Date: 2026-04-30
"""

import sqlalchemy as sa
from alembic import op

revision = "20260430_00"
down_revision = "20260429_00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("approvals", sa.Column("send_provider", sa.String(length=32), nullable=True))
    op.add_column(
        "approvals",
        sa.Column("delivery_status", sa.String(length=32), nullable=False, server_default="not_sent"),
    )
    op.add_column("approvals", sa.Column("delivery_error", sa.Text(), nullable=True))
    op.add_column("approvals", sa.Column("provider_message_id", sa.String(length=255), nullable=True))
    op.add_column("approvals", sa.Column("provider_thread_id", sa.String(length=255), nullable=True))
    op.add_column("approvals", sa.Column("provider_confirmed_at", sa.DateTime(timezone=True), nullable=True))

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
