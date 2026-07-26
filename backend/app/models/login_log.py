from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LoginLog(Base):
    """Answers 'who logged in (or tried to)?' — see AuditLog for 'what did
    they do?'. `user_id` is nullable so attempts against unknown emails are
    still recorded (enumeration / brute-force monitoring); `attempted_email`
    preserves what was typed even when it doesn't resolve to a user."""

    __tablename__ = "login_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    attempted_email: Mapped[str] = mapped_column(String(128), nullable=False)

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device: Mapped[str | None] = mapped_column(String(256), nullable=True)
    login_time: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success / failed
