from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.security.encryption import EncryptedString


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("doctors.id"), nullable=True)

    # Encrypted at rest
    encrypted_symptoms: Mapped[str | None] = mapped_column(EncryptedString(1024), nullable=True)
    encrypted_diagnosis: Mapped[str | None] = mapped_column(EncryptedString(1024), nullable=True)
    encrypted_lab_result: Mapped[str | None] = mapped_column(EncryptedString(1024), nullable=True)
    
    encrypted_prescription: Mapped[str | None] = mapped_column(EncryptedString(1024), nullable=True)
    encrypted_prescribed_tests: Mapped[str | None] = mapped_column(EncryptedString(1024), nullable=True)
    encrypted_medical_history: Mapped[str | None] = mapped_column(EncryptedString(2048), nullable=True)
    encrypted_clinical_history: Mapped[str | None] = mapped_column(EncryptedString(2048), nullable=True)
    encrypted_doctor_note: Mapped[str | None] = mapped_column(EncryptedString(2048), nullable=True)

    # ML diagnosis-prediction outcome for this record (if run)
    ml_dengue_predicted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ml_dengue_probability: Mapped[float | None] = mapped_column(Float, nullable=True)

    date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="medical_records")
