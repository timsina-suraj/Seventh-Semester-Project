from sqlalchemy import select

from app.models.doctor_availability import DoctorAvailability
from app.repositories.base import BaseRepository


class DoctorAvailabilityRepository(BaseRepository[DoctorAvailability]):
    model = DoctorAvailability

    async def list_for_doctor(self, doctor_id: int) -> list[DoctorAvailability]:
        return await self.list(doctor_id=doctor_id)

    async def list_for_doctor_and_day(self, doctor_id: int, day_of_week: int) -> list[DoctorAvailability]:
        result = await self.db.execute(
            select(DoctorAvailability).where(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.day_of_week == day_of_week,
            )
        )
        return list(result.scalars().all())
