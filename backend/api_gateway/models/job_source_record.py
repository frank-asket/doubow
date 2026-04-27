from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.session import Base


class JobSourceRecord(Base):
    __tablename__ = "job_source_records"
    __table_args__ = (UniqueConstraint("provider", "provider_job_id", name="uq_job_source_records_provider_job"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_job_id: Mapped[str] = mapped_column(String(255))
    raw_payload: Mapped[dict] = mapped_column(JSON)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
