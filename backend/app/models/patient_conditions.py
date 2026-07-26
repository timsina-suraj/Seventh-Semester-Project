from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

VALID_CONDITION_STATUSES = ("Active", "Resolved", "Managed")


class PatientCondition(Base):
    """Chronic/ongoing conditions (diabetes, hypertension, ...) — distinct
    from `medical_history` (past discrete diagnoses) in that these have an
    ongoing `status` and directly feed the dengue risk model's comorbidity
    features (Module 17: Diabetes, Hypertension, Obesity, Pregnancy)."""

    __tablename__ = "patient_conditions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False, index=True)

    condition: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Active")  # one of VALID_CONDITION_STATUSES
    diagnosed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
