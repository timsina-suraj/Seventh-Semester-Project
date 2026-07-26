from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    employee_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str] = mapped_column(String(128), nullable=False)
    specialization: Mapped[str] = mapped_column(String(128), nullable=False, default="General Physician")
    license_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    appointments = relationship("Appointment", back_populates="doctor")
    availability_slots = relationship(
        "DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan"
    )
