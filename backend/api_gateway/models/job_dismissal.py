from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    from models.job import Job
    from models.user import User


class JobDismissal(Base):
    """User hid a job from Discover; do not auto-resurface a score for it."""

    __tablename__ = "job_dismissals"

    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True)

    user: Mapped["User"] = relationship("User", back_populates="job_dismissals")
    job: Mapped["Job"] = relationship("Job", back_populates="dismissals")
