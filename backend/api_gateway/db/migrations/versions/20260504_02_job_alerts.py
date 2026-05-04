"""Add job alert subscriptions and delivery tracking.

Revision ID: 20260504_02
Revises: 20260504_01
Create Date: 2026-05-04
"""

from alembic import op
import sqlalchemy as sa

revision = "20260504_02"
down_revision = "20260504_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_alert_subscriptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("frequency", sa.String(length=16), nullable=False, server_default="daily"),
        sa.Column("min_fit", sa.Numeric(3, 1), nullable=False, server_default="4.0"),
        sa.Column("max_items", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_job_alert_subscriptions_user"),
    )
    op.create_index("ix_job_alert_subscriptions_user_id", "job_alert_subscriptions", ["user_id"], unique=False)

    op.create_table(
        "job_alert_deliveries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), nullable=True),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("fit_score", sa.Numeric(3, 1), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subscription_id"], ["job_alert_subscriptions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id", name="uq_job_alert_deliveries_user_job"),
    )
    op.create_index("ix_job_alert_deliveries_user_id", "job_alert_deliveries", ["user_id"], unique=False)
    op.create_index("ix_job_alert_deliveries_subscription_id", "job_alert_deliveries", ["subscription_id"], unique=False)
    op.create_index("ix_job_alert_deliveries_job_id", "job_alert_deliveries", ["job_id"], unique=False)

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            ALTER TABLE job_alert_subscriptions ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS doubow_job_alert_subscriptions_tenant ON job_alert_subscriptions;
            CREATE POLICY doubow_job_alert_subscriptions_tenant ON job_alert_subscriptions
              FOR ALL
              USING (user_id = public.doubow_current_user_id())
              WITH CHECK (user_id = public.doubow_current_user_id());
            """
        )
        op.execute(
            """
            ALTER TABLE job_alert_deliveries ENABLE ROW LEVEL SECURITY;
            DROP POLICY IF EXISTS doubow_job_alert_deliveries_tenant ON job_alert_deliveries;
            CREATE POLICY doubow_job_alert_deliveries_tenant ON job_alert_deliveries
              FOR ALL
              USING (user_id = public.doubow_current_user_id())
              WITH CHECK (user_id = public.doubow_current_user_id());
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP POLICY IF EXISTS doubow_job_alert_deliveries_tenant ON job_alert_deliveries;")
        op.execute("ALTER TABLE job_alert_deliveries DISABLE ROW LEVEL SECURITY;")
        op.execute("DROP POLICY IF EXISTS doubow_job_alert_subscriptions_tenant ON job_alert_subscriptions;")
        op.execute("ALTER TABLE job_alert_subscriptions DISABLE ROW LEVEL SECURITY;")

    op.drop_index("ix_job_alert_deliveries_job_id", table_name="job_alert_deliveries")
    op.drop_index("ix_job_alert_deliveries_subscription_id", table_name="job_alert_deliveries")
    op.drop_index("ix_job_alert_deliveries_user_id", table_name="job_alert_deliveries")
    op.drop_table("job_alert_deliveries")

    op.drop_index("ix_job_alert_subscriptions_user_id", table_name="job_alert_subscriptions")
    op.drop_table("job_alert_subscriptions")
