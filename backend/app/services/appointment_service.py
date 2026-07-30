from datetime import datetime, timedelta, timezone

from app.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.appointment import VALID_STATUSES, Appointment
from app.repositories.appointment_repository import AppointmentRepository
from app.services.audit_service import AuditService
from app.services.doctor_availability_service import DoctorAvailabilityService


def _as_naive_utc(dt: datetime) -> datetime:
    """SQLite silently drops tzinfo on round-trip, so every appointment_date
    already in the DB comes back naive — normalize any incoming datetime the
    same way before storing/comparing, or aware-vs-naive subtraction below
    raises TypeError."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


class AppointmentService:
    def __init__(
        self,
        appointment_repo: AppointmentRepository,
        availability_service: DoctorAvailabilityService,
        audit_service: AuditService,
    ):
        self.appointment_repo = appointment_repo
        self.availability_service = availability_service
        self.audit_service = audit_service

    async def book(
        self, patient_id: int, doctor_id: int, appointment_date: datetime, reason: str | None, actor_user_id: int
    ) -> Appointment:
        appointment_date = _as_naive_utc(appointment_date)

        now = _as_naive_utc(datetime.now(timezone.utc))
        if appointment_date < now:
            raise ValidationError("appointment_date cannot be in the past")

        if not await self.availability_service.is_within_availability(doctor_id, appointment_date):
            raise ValidationError(
                "Doctor is not available at this time — check GET /doctors/{id}/available-slots"
            )

        step = timedelta(minutes=settings.appointment_slot_minutes)
        window = await self.appointment_repo.list_active_for_doctor_between(
            doctor_id, appointment_date - step, appointment_date + step
        )
        overlapping = any(
            abs((a.appointment_date - appointment_date).total_seconds()) < step.total_seconds()
            for a in window
        )
        if overlapping:
            raise ValidationError("Doctor already has an appointment at this time")

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            reason=reason,
            status="Pending",
        )
        self.appointment_repo.add(appointment)
        await self.appointment_repo.commit()
        await self.appointment_repo.refresh(appointment)

        await self.audit_service.record(actor_user_id, "booked_appointment", "appointment", appointment.id)
        return appointment

    async def update_status(self, appointment_id: int, new_status: str, actor_user_id: int) -> Appointment:
        if new_status not in VALID_STATUSES:
            raise ValidationError(f"status must be one of {VALID_STATUSES}")

        appointment = await self.appointment_repo.get(appointment_id)
        if not appointment:
            raise NotFoundError("Appointment not found")

        appointment.status = new_status
        await self.appointment_repo.commit()
        await self.appointment_repo.refresh(appointment)

        await self.audit_service.record(
            actor_user_id, f"appointment_marked_{new_status.lower().replace('-', '_')}", "appointment", appointment.id
        )
        return appointment
