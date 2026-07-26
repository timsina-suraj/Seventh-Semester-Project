from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

VALID_DOCUMENT_CATEGORIES = ("Lab Report", "Prescription", "Insurance", "ID Proof", "Other")


class Document(Base):
    """Module 12: patient-linked file uploads. Files live on disk under
    settings.upload_dir, named by a random token (`stored_filename`) so a
    guessed/incremented URL can't be used to fetch someone else's file —
    only the DB row (behind an authorization check) maps id -> file."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)
    uploaded_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient")
    uploaded_by = relationship("User")
