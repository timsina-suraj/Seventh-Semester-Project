from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MedicineAdministration(Base):
    """Module 6's optional medication-administration log — a nurse
    recording that a dose was actually given, distinct from the doctor's
    Prescription (what should be given)."""

    __tablename__ = "medicine_administration"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    nurse_id: Mapped[int] = mapped_column(ForeignKey("nurses.id"), nullable=False)

    medicine: Mapped[str] = mapped_column(String(128), nullable=False)
    dose: Mapped[str | None] = mapped_column(String(64), nullable=True)
    time_given: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
