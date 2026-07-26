from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.security.encryption import EncryptedString

VALID_GENDERS = ("Male", "Female", "Other")
VALID_BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    # System-issued on registration, e.g. "PAT-2026-0050" — see
    # PatientRepository.next_patient_number().
    patient_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)  # one of VALID_GENDERS
    blood_group: Mapped[str] = mapped_column(String(10), nullable=False, default="Unknown")

    # Encrypted at rest (AES-256-GCM via EncryptedString), decrypted only on
    # authorized read.
    encrypted_phone: Mapped[str | None] = mapped_column(EncryptedString(256), nullable=True)
    # JSON blob of {"province": ..., "municipality": ...} — see the district
    # note below for why district itself is not inside this blob.
    encrypted_address: Mapped[str | None] = mapped_column(EncryptedString(512), nullable=True)
    encrypted_emergency_contact: Mapped[str | None] = mapped_column(EncryptedString(256), nullable=True)

    # Plain + indexed (not part of the encrypted address blob): the district
    # risk map, alerts-by-district, and the dengue ML feature pipeline all
    # need it as a queryable, joinable value against the 62-district climate
    # dataset. Province/municipality (more identifying) stay encrypted.
    district: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    user = relationship("User")
