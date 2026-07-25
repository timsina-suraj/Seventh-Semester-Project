from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

VALID_ROLES = ("admin", "doctor", "receptionist", "patient")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # one of VALID_ROLES
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # True right after an admin/receptionist creates the account with a
    # system-generated one-time password; forced to False once the user sets
    # their own password via POST /auth/change-password.
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    reset_otp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reset_otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))