"""Computes real open appointment slots from a doctor's declared weekly
availability minus already-booked appointments (Module 1 + Module 7:
'real appointment-conflict validation')."""
from datetime import date, datetime, time, timedelta

from app.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.doctor_availability import DoctorAvailability
from app.models.user import User
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_availability_repository import DoctorAvailabilityRepository
from app.repositories.staff_repository import DoctorRepository


class DoctorAvailabilityService:
    def __init__(
        self,
        availability_repo: DoctorAvailabilityRepository,
        doctor_repo: DoctorRepository,
        appointment_repo: AppointmentRepository,
    ):
        self.availability_repo = availability_repo
        self.doctor_repo = doctor_repo
        self.appointment_repo = appointment_repo

    async def _check_ownership(self, doctor_id: int, actor: User) -> None:
        if actor.role == "admin":
            return
        if actor.role == "doctor":
            doctor = await self.doctor_repo.get_by_user_id(actor.id)
            if doctor and doctor.id == doctor_id:
                return
        raise ForbiddenError("Not authorized to manage this doctor's availability")

    async def list_slots(self, doctor_id: int) -> list[DoctorAvailability]:
        return await self.availability_repo.list_for_doctor(doctor_id)

    async def add_slot(
        self, doctor_id: int, day_of_week: int, start_time: time, end_time: time, actor: User
    ) -> DoctorAvailability:
        await self._check_ownership(doctor_id, actor)
        slot = DoctorAvailability(
            doctor_id=doctor_id, day_of_week=day_of_week, start_time=start_time, end_time=end_time
        )
        self.availability_repo.add(slot)
        await self.availability_repo.commit()
        await self.availability_repo.refresh(slot)
        return slot

    async def remove_slot(self, doctor_id: int, slot_id: int, actor: User) -> None:
        await self._check_ownership(doctor_id, actor)
        slot = await self.availability_repo.get(slot_id)
        if not slot or slot.doctor_id != doctor_id:
            raise NotFoundError("Availability slot not found")
        await self.availability_repo.delete(slot)
        await self.availability_repo.commit()

    async def is_within_availability(self, doctor_id: int, appointment_dt: datetime) -> bool:
        slots = await self.availability_repo.list_for_doctor_and_day(doctor_id, appointment_dt.weekday())
        t = appointment_dt.time()
        return any(slot.start_time <= t < slot.end_time for slot in slots)

    async def available_slots_on(self, doctor_id: int, on_date: date) -> list[time]:
        """Open start-times for a given day: the doctor's availability
        window(s), stepped by APPOINTMENT_SLOT_MINUTES, minus times that
        already have an active (Pending/Confirmed) appointment."""
        slots = await self.availability_repo.list_for_doctor_and_day(doctor_id, on_date.weekday())
        if not slots:
            return []

        step = timedelta(minutes=settings.appointment_slot_minutes)
        day_start = datetime.combine(on_date, time.min)
        day_end = datetime.combine(on_date, time.max)
        booked = await self.appointment_repo.list_active_for_doctor_between(doctor_id, day_start, day_end)
        booked_starts = {a.appointment_date.replace(second=0, microsecond=0) for a in booked}

        open_times: list[time] = []
        for slot in slots:
            cursor = datetime.combine(on_date, slot.start_time)
            slot_end = datetime.combine(on_date, slot.end_time)
            while cursor + step <= slot_end:
                if cursor not in booked_starts:
                    open_times.append(cursor.time())
                cursor += step
        return sorted(open_times)
