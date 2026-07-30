from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

VALID_ALERT_STATUSES = ("open", "acknowledged", "resolved")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alert_type: Mapped[str] = mapped_column(String(32), nullable=False)  # district_risk / patient_diagnosis
    district: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open")  # one of VALID_ALERT_STATUSES
    date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
