from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.lab_test import LabTest
from app.models.medical_record import MedicalRecord
from app.models.medicine import Medicine
from app.models.patient import Patient
from app.schemas.dashboard import HospitalStats


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

    return HospitalStats(
        total_patients=total_patients or 0,
        dengue_cases_flagged=dengue_cases_flagged or 0,
        available_doctors=total_doctors or 0,
        total_appointments=total_appointments or 0,
        total_lab_results=total_lab_results or 0,
        low_stock_items=low_stock_items,
        open_alerts=open_alerts or 0,
    )
