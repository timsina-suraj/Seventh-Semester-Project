from datetime import datetime

from sqlalchemy import select

from app.models.appointment import ACTIVE_STATUSES, Appointment
from app.repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    model = Appointment

    async def list_active_for_doctor_between(
        self, doctor_id: int, start: datetime, end: datetime
    ) -> list[Appointment]:
        """Active (Pending/Confirmed) appointments for a doctor whose
        `appointment_date` falls in [start, end) — used for overlap
        checking against a candidate slot."""
        result = await self.db.execute(
            select(Appointment).where(
                Appointment.doctor_id == doctor_id,
                Appointment.status.in_(ACTIVE_STATUSES),
                Appointment.appointment_date >= start,
                Appointment.appointment_date < end,
            )
        )
        return list(result.scalars().all())

    async def list_filtered(
        self,
        patient_id: int | None = None,
        doctor_id: int | None = None,
        status: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Appointment]:
        stmt = select(Appointment)
        if patient_id is not None:
            stmt = stmt.where(Appointment.patient_id == patient_id)
        if doctor_id is not None:
            stmt = stmt.where(Appointment.doctor_id == doctor_id)
        if status is not None:
            stmt = stmt.where(Appointment.status == status)
        if date_from is not None:
            stmt = stmt.where(Appointment.appointment_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Appointment.appointment_date < date_to)
        stmt = stmt.order_by(Appointment.appointment_date.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
