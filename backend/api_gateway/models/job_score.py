from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class JobScore(Base):
    __tablename__ = "job_scores"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_job_scores_user_job"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    fit_score: Mapped[float] = mapped_column(Numeric(3, 1))
    fit_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    risk_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    dimension_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    provenance: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown", server_default="unknown")

    user = relationship("User", back_populates="job_scores")
    job = relationship("Job", back_populates="scores")
