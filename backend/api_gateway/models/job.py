from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    from models.application import Application
    from models.job_dismissal import JobDismissal
    from models.job_score import JobScore


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_jobs_source_external_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source: Mapped[str] = mapped_column(String(64), index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    #: When set, Discover bootstraps a per-user `job_scores` row from this payload (until dismissed).
    score_template: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    applications: Mapped[list["Application"]] = relationship("Application", back_populates="job")
    scores: Mapped[list["JobScore"]] = relationship("JobScore", back_populates="job", cascade="all, delete-orphan")
    dismissals: Mapped[list["JobDismissal"]] = relationship(
        "JobDismissal", back_populates="job", cascade="all, delete-orphan"
    )
