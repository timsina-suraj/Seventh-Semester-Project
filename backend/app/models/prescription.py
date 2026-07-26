from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False)
    medical_record_id: Mapped[int | None] = mapped_column(ForeignKey("medical_records.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    items = relationship("PrescriptionItem", back_populates="prescription", cascade="all, delete-orphan")


class PrescriptionItem(Base):
    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"), nullable=False)

    medicine_name: Mapped[str] = mapped_column(String(128), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    prescription = relationship("Prescription", back_populates="items")
