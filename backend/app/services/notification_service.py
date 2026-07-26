"""Module 13: fire-and-forget patient notifications. Kept separate from the
clinical services (AppointmentService, LabService, PrescriptionService) so
those stay free of email/BackgroundTasks concerns — routers call this after
the underlying action succeeds."""
from fastapi import BackgroundTasks

from app.core.logging import get_logger
from app.models.appointment import Appointment
from app.models.lab_test import LabTest
from app.models.prescription import Prescription
from app.repositories.patient_repository import PatientRepository
from app.services.email_service import (
    send_appointment_booked_email,
    send_appointment_status_email,
    send_lab_result_ready_email,
    send_prescription_ready_email,
)

logger = get_logger(__name__)


class NotificationService:
    def __init__(self, patient_repo: PatientRepository):
        self.patient_repo = patient_repo

    def _dispatch(self, background_tasks: BackgroundTasks | None, fn, *args) -> None:
        if background_tasks is not None:
            background_tasks.add_task(fn, *args)
        else:
            fn(*args)

    async def _patient_email(self, patient_id: int) -> str | None:
        patient = await self.patient_repo.get(patient_id)
        if not patient or not patient.user:
            logger.warning("notification_skipped_no_patient_email patient_id=%s", patient_id)
            return None
        return patient.user.email

    async def notify_appointment_booked(
        self, appointment: Appointment, doctor_name: str, background_tasks: BackgroundTasks | None = None
    ) -> None:
        email = await self._patient_email(appointment.patient_id)
        if not email:
            return
        self._dispatch(
            background_tasks,
            send_appointment_booked_email,
            email,
            doctor_name,
            appointment.appointment_date.isoformat(),
            appointment.reason,
        )

    async def notify_appointment_status_changed(
        self, appointment: Appointment, background_tasks: BackgroundTasks | None = None
    ) -> None:
        email = await self._patient_email(appointment.patient_id)
        if not email:
            return
        self._dispatch(
            background_tasks,
            send_appointment_status_email,
            email,
            appointment.appointment_date.isoformat(),
            appointment.status,
        )

    async def notify_lab_result_ready(
        self, lab_test: LabTest, background_tasks: BackgroundTasks | None = None
    ) -> None:
        email = await self._patient_email(lab_test.patient_id)
        if not email:
            return
        self._dispatch(background_tasks, send_lab_result_ready_email, email, lab_test.test_name)

    async def notify_prescription_created(
        self, prescription: Prescription, doctor_name: str, background_tasks: BackgroundTasks | None = None
    ) -> None:
        email = await self._patient_email(prescription.patient_id)
        if not email:
            return
        self._dispatch(
            background_tasks, send_prescription_ready_email, email, doctor_name, len(prescription.items)
        )
