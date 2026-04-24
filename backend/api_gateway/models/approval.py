from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    from models.application import Application
    from models.user import User


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (UniqueConstraint("user_id", "idempotency_key", name="uq_approvals_user_idempotency"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), index=True)
    type: Mapped[str] = mapped_column(String(64))
    channel: Mapped[str] = mapped_column(String(32))
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    draft_body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    send_provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(32), default="not_sent")
    delivery_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="approvals")
    application: Mapped["Application"] = relationship("Application", back_populates="approvals")
