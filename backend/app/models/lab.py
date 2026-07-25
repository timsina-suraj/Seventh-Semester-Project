from datetime import datetime, timezone

from sqlalchemy import Integer, Float, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LabResult(Base):
    """Stores raw dengue test / blood panel data used both clinically and as
    ML classifier input (per spec 5.8 Laboratory Management Module)."""

    __tablename__ = "lab_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)

    ns1_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    igg_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    igm_positive: Mapped[bool] = mapped_column(Boolean, default=False)

    fever_duration_days: Mapped[int] = mapped_column(Integer, default=0)
    body_temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    platelet_count: Mapped[int] = mapped_column(Integer, nullable=False)
    wbc_count: Mapped[int] = mapped_column(Integer, nullable=False)

    joint_pain: Mapped[str] = mapped_column(String(20), default="None")  # None/Moderate/Severe
    headache: Mapped[bool] = mapped_column(Boolean, default=False)
    retro_orbital_pain: Mapped[bool] = mapped_column(Boolean, default=False)
    myalgia: Mapped[bool] = mapped_column(Boolean, default=False)
    rash: Mapped[bool] = mapped_column(Boolean, default=False)

    dengue_test_result: Mapped[str] = mapped_column(String(20), default="Pending")  # Positive/Negative/Pending

    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="lab_results")
