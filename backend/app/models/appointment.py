from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

VALID_STATUSES = ("Pending", "Confirmed", "Completed", "Cancelled", "No-show")
ACTIVE_STATUSES = ("Pending", "Confirmed")  # count towards conflict/overlap checks


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)

    appointment_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Pending")  # one of VALID_STATUSES

    created_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
