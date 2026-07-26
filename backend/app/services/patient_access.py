"""Shared "which patients can this doctor see" rule — a doctor is allowed to
see a patient if they have an appointment or an authored medical record with
them. Used by every router that scopes patient-linked data (patients,
documents, ...) to a doctor's own caseload."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord


async def doctor_patient_ids(db: AsyncSession, doctor_id: int) -> set[int]:
    appt_ids = select(Appointment.patient_id).where(Appointment.doctor_id == doctor_id)
    record_ids = select(MedicalRecord.patient_id).where(MedicalRecord.doctor_id == doctor_id)
    result = await db.execute(appt_ids.union(record_ids))
    return {row[0] for row in result.all()}
