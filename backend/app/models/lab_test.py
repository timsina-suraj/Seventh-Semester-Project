from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

VALID_LAB_TEST_STATUSES = ("Requested", "Completed", "Cancelled")


class LabTest(Base):
    """The request half of Module 10's workflow: Doctor requests a test ->
    Lab Technician uploads a result (see LabResult) -> Doctor reviews ->
    Patient views."""

    __tablename__ = "lab_tests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)

    test_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Requested")  # one of VALID_LAB_TEST_STATUSES
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    result = relationship("LabResult", back_populates="lab_test", uselist=False, cascade="all, delete-orphan")
