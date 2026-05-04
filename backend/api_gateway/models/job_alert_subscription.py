from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    from models.job_alert_delivery import JobAlertDelivery
    from models.user import User


class JobAlertSubscription(Base):
    __tablename__ = "job_alert_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", name="uq_job_alert_subscriptions_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="daily", server_default="daily")
    min_fit: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False, default=4.0, server_default="4.0")
    max_items: Mapped[int] = mapped_column(nullable=False, default=5, server_default="5")
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="job_alert_subscription")
    deliveries: Mapped[list["JobAlertDelivery"]] = relationship(
        "JobAlertDelivery",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )
