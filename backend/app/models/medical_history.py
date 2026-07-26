from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.security.encryption import EncryptedString


class MedicalHistory(Base):
    """Structured replacement for the old free-text
    `encrypted_medical_history` blob that used to live on every
    `medical_records` row — one row per past condition instead of a
    re-typed paragraph per visit."""

    __tablename__ = "medical_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)

    condition_name: Mapped[str] = mapped_column(EncryptedString(256), nullable=False)
    diagnosed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(EncryptedString(1024), nullable=True)
