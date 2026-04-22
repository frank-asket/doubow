from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base

if TYPE_CHECKING:
    from models.user import User


class GoogleOAuthCredential(Base):
    """Stored refresh token for Gmail API (OAuth2)."""

    __tablename__ = "google_oauth_credentials"

    user_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    refresh_token_encrypted: Mapped[str] = mapped_column(Text)
    google_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    scopes: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="google_oauth")
