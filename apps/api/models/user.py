from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    from models.application import Application
    from models.approval import Approval
    from models.autopilot_run import AutopilotRun
    from models.job_score import JobScore
    from models.prep_session import PrepSession
    from models.resume import Resume


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    plan: Mapped[str] = mapped_column(String(32), default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    resumes: Mapped[list["Resume"]] = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications: Mapped[list["Application"]] = relationship(
        "Application", back_populates="user", cascade="all, delete-orphan"
    )
    approvals: Mapped[list["Approval"]] = relationship("Approval", back_populates="user", cascade="all, delete-orphan")
    autopilot_runs: Mapped[list["AutopilotRun"]] = relationship(
        "AutopilotRun", back_populates="user", cascade="all, delete-orphan"
    )
    prep_sessions: Mapped[list["PrepSession"]] = relationship(
        "PrepSession", back_populates="user", cascade="all, delete-orphan"
    )
    job_scores: Mapped[list["JobScore"]] = relationship("JobScore", back_populates="user", cascade="all, delete-orphan")
