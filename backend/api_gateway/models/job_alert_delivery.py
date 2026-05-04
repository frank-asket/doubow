from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    from models.job import Job
    from models.job_alert_subscription import JobAlertSubscription
    from models.user import User


class JobAlertDelivery(Base):
    __tablename__ = "job_alert_deliveries"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_job_alert_deliveries_user_job"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subscription_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("job_alert_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    fit_score: Mapped[float] = mapped_column(Numeric(3, 1), nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="job_alert_deliveries")
    subscription: Mapped["JobAlertSubscription | None"] = relationship("JobAlertSubscription", back_populates="deliveries")
    job: Mapped["Job"] = relationship("Job")
