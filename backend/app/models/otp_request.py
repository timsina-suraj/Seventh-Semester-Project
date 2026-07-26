from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

VALID_OTP_PURPOSES = ("first_login", "password_reset")


class OtpRequest(Base):
    """One row per OTP issued. Never stores the OTP itself — only its hash.

    Superseded by a fresh row on every re-request (the previous row is left
    in place for audit purposes; only the newest unused, unexpired row for
    a given (user_id, purpose) is considered active — see OtpService).
    """

    __tablename__ = "otp_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(20), nullable=False)  # one of VALID_OTP_PURPOSES
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
