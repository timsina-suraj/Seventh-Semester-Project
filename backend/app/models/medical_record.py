from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.security.encryption import EncryptedString


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("doctors.id"), nullable=True)
    # Nullable: real consultations link one, but the ad-hoc dengue-check
    # flow (Module 17) creates a record with no appointment context.
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"), nullable=True)

    encrypted_symptoms: Mapped[str | None] = mapped_column(EncryptedString(1024), nullable=True)
    encrypted_diagnosis: Mapped[str | None] = mapped_column(EncryptedString(1024), nullable=True)
    encrypted_notes: Mapped[str | None] = mapped_column(EncryptedString(2048), nullable=True)
    encrypted_treatment_plan: Mapped[str | None] = mapped_column(EncryptedString(2048), nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # ML diagnosis-prediction outcome for this record (if run) — kept beyond
    # spec's literal column list because the existing /ml/predict/patient
    # endpoint (Module 17) already writes these; dropping them would break
    # a working feature.
    ml_dengue_predicted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ml_dengue_probability: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="medical_records")
