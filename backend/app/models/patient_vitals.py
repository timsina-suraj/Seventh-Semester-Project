from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PatientVitals(Base):
    __tablename__ = "patient_vitals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    nurse_id: Mapped[int] = mapped_column(ForeignKey("nurses.id"), nullable=False)

    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    blood_pressure: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "120/80"
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    oxygen_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
