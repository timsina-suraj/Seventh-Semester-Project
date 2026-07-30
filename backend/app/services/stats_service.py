from datetime import datetime, timedelta, timezone

from sqlalchemy import Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.lab_test import LabTest
from app.models.medical_record import MedicalRecord
from app.models.medicine import Medicine
from app.models.patient import Patient
from app.schemas.dashboard import HospitalStats, TrendPoint


async def _daily_trend(db: AsyncSession, date_column, days: int) -> list[TrendPoint]:
    """One TrendPoint per day for the last `days` days (today inclusive),
    zero-filled so every day appears even with no activity. Uses UTC time
    to match the codebase's established convention for timestamps."""
    start = datetime.now(timezone.utc).date() - timedelta(days=days - 1)
    day_expr = func.date(date_column, type_=Date)
    stmt = (
        select(day_expr.label("day"), func.count().label("cnt"))
        .where(date_column >= start)
        .group_by(day_expr)
    )
    result = await db.execute(stmt)
    counts = {row.day.isoformat(): row.cnt for row in result.all()}
    return [
        TrendPoint(
            date=(start + timedelta(days=i)).isoformat(),
            count=counts.get((start + timedelta(days=i)).isoformat(), 0),
        )
        for i in range(days)
    ]


async def get_hospital_stats(db: AsyncSession) -> HospitalStats:
    total_patients = await db.scalar(select(func.count()).select_from(Patient))
    dengue_cases_flagged = await db.scalar(
        select(func.count()).select_from(MedicalRecord).where(MedicalRecord.ml_dengue_predicted.is_(True))
    )
    total_doctors = await db.scalar(select(func.count()).select_from(Doctor))
    total_appointments = await db.scalar(select(func.count()).select_from(Appointment))
    total_lab_results = await db.scalar(select(func.count()).select_from(LabTest))

    medicines_result = await db.execute(select(Medicine).options(selectinload(Medicine.inventory)))
    low_stock_items = sum(
        1 for m in medicines_result.scalars().all() if m.inventory and m.inventory.is_low_stock
    )

    open_alerts = await db.scalar(select(func.count()).select_from(Alert).where(Alert.status == "open"))

    appointments_trend = await _daily_trend(db, Appointment.appointment_date, 14)
    registrations_trend = await _daily_trend(db, Patient.created_at, 30)

    return HospitalStats(
        total_patients=total_patients or 0,
        dengue_cases_flagged=dengue_cases_flagged or 0,
        available_doctors=total_doctors or 0,
        total_appointments=total_appointments or 0,
        total_lab_results=total_lab_results or 0,
        low_stock_items=low_stock_items,
        open_alerts=open_alerts or 0,
        appointments_trend=appointments_trend,
        registrations_trend=registrations_trend,
    )
