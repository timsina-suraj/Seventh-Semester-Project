from datetime import datetime

from sqlalchemy import select

from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord
from app.repositories.base import BaseRepository


class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    model = MedicalRecord

    async def list_filtered(
        self,
        patient_id: int | None = None,
        doctor_id: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[MedicalRecord]:
        """`diagnosis` filtering isn't done here — encrypted_diagnosis is
        AES-256-GCM encrypted with a random nonce per value, so equal
        plaintexts never produce equal ciphertext and a SQL LIKE/ilike can
        never match it. Callers filter by diagnosis in Python after this
        query narrows the set down by the plaintext columns below."""
        stmt = select(MedicalRecord)
        if patient_id is not None:
            stmt = stmt.where(MedicalRecord.patient_id == patient_id)
        if doctor_id is not None:
            stmt = stmt.where(MedicalRecord.doctor_id == doctor_id)
        if date_from is not None:
            stmt = stmt.where(MedicalRecord.created_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(MedicalRecord.created_at < date_to)
        stmt = stmt.order_by(MedicalRecord.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_for_doctor(self, doctor_id: int) -> list[MedicalRecord]:
        """Records a doctor authored directly, or that belong to a patient
        via one of the doctor's own appointments — mirrors the existing
        doctor-scoping logic already used for /patients."""
        result = await self.db.execute(
            select(MedicalRecord).where(
                MedicalRecord.patient_id.in_(
                    select(Appointment.patient_id)
                    .where(Appointment.doctor_id == doctor_id)
                    .union(select(MedicalRecord.patient_id).where(MedicalRecord.doctor_id == doctor_id))
                )
            )
        )
        return list(result.scalars().all())
