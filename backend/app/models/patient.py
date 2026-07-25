from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.security.encryption import EncryptedString


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)

    # Encrypted at rest (AES-256-GCM via EncryptedString)
    encrypted_name: Mapped[str] = mapped_column(EncryptedString(512), nullable=False)
    encrypted_address: Mapped[str | None] = mapped_column(EncryptedString(512), nullable=True)
    encrypted_phone: Mapped[str | None] = mapped_column(EncryptedString(256), nullable=True)

    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)  # Male / Female / Other
    district: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="patient", cascade="all, delete-orphan")
    user = relationship("User")