from datetime import time

from sqlalchemy import ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# 0=Monday .. 6=Sunday (Python's datetime.weekday() convention), so
# appointment-conflict validation (Phase B) can compare directly against
# `appointment_date.weekday()` without a lookup table.
DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)

    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday .. 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    doctor = relationship("Doctor", back_populates="availability_slots")
