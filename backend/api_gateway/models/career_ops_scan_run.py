from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    from models.user import User


class CareerOpsScanRun(Base):
    __tablename__ = "career_ops_scan_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True, default="queued")

    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sources_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    max_results: Mapped[int] = mapped_column(Integer, default=100)
    min_fit_threshold: Mapped[float] = mapped_column(Numeric(3, 1), default=0.0)
    queue_top_n: Mapped[int] = mapped_column(Integer, default=0)

    fetched: Mapped[int] = mapped_column(Integer, default=0)
    inserted: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    deduped: Mapped[int] = mapped_column(Integer, default=0)
    scored: Mapped[int] = mapped_column(Integer, default=0)
    kept_after_threshold: Mapped[int] = mapped_column(Integer, default=0)
    queued_to_pipeline: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_mix_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    top_job_ids_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped["User"] = relationship("User", back_populates="career_ops_scan_runs")
