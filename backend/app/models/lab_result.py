from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LabResult(Base):
    """The result half of Module 10's workflow, uploaded by a Lab
    Technician against an existing LabTest request.

    `result_file` is a placeholder filename/path column for now — real file
    upload/storage is Module 12 (Document Management, Phase C). Structured
    `result_value` is what's actually usable today, and what Phase D's ML
    feature pipeline will read (e.g. platelet counts by test_name/date)."""

    __tablename__ = "lab_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    lab_test_id: Mapped[int] = mapped_column(ForeignKey("lab_tests.id"), unique=True, nullable=False)

    result_file: Mapped[str | None] = mapped_column(String(256), nullable=True)
    result_value: Mapped[str | None] = mapped_column(String(256), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    lab_test = relationship("LabTest", back_populates="result")
