from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    from models.approval import Approval
    from models.job import Job
    from models.prep_session import PrepSession
    from models.user import User


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="saved")
    channel: Mapped[str] = mapped_column(String(32))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False)
    dedup_group: Mapped[str | None] = mapped_column(String(36), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="applications")
    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    approvals: Mapped[list["Approval"]] = relationship("Approval", back_populates="application", cascade="all, delete-orphan")
    prep_sessions: Mapped[list["PrepSession"]] = relationship(
        "PrepSession", back_populates="application", cascade="all, delete-orphan"
    )
