from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

VALID_ROLES = ("admin", "doctor", "nurse", "receptionist", "lab_technician", "patient")
VALID_STAFF_ROLES = ("doctor", "nurse", "receptionist", "lab_technician")


class User(Base):
    """Common authentication table — login + security info only.

    Role-specific profile data lives in its own table (Admin, Doctor, Nurse,
    Receptionist, LabTechnician, Patient), each holding a `user_id` FK back
    here. OTP material lives in `otp_requests`, not on this row.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)

    # Null until the user completes the first-login OTP flow and sets a
    # password of their own (see OtpService / AuthService).
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # one of VALID_ROLES

    # False until the account is activated via the first-login OTP flow.
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # True from account creation until the user sets their own password.
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
