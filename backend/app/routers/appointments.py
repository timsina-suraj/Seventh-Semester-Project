from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.database import get_db
from app.dependencies import (
    get_appointment_repository,
    get_appointment_service,
    get_doctor_repository,
    get_notification_service,
    get_patient_repository,
)
from app.models.doctor import Doctor
from app.models.user import User
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.staff_repository import DoctorRepository
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdateStatus
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.appointment_service import AppointmentService
from app.services.notification_service import NotificationService
from app.services.pdf_service import build_appointment_receipt_pdf

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post(
    "",
    response_model=AppointmentRead,
    dependencies=[Depends(require_role("admin", "receptionist"))],
)
async def create_appointment(
    payload: AppointmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    service: AppointmentService = Depends(get_appointment_service),
    notification_service: NotificationService = Depends(get_notification_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    current_user: User = Depends(get_current_user),
):
    if not await patient_repo.get(payload.patient_id):
        raise NotFoundError("Patient not found")
    doctor = await db.get(Doctor, payload.doctor_id)
    if not doctor:
        raise NotFoundError("Doctor not found")

    appointment = await service.book(
        payload.patient_id, payload.doctor_id, payload.appointment_date, payload.reason, current_user.id
    )
    await notification_service.notify_appointment_booked(appointment, doctor.full_name, background_tasks)
    return appointment


@router.get("", response_model=list[AppointmentRead])
async def list_appointments(
    repo: AppointmentRepository = Depends(get_appointment_repository),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    current_user: User = Depends(get_current_user),
    doctor_id: int | None = None,
    patient_id: int | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    # date_to is inclusive of the whole day on the frontend's terms, so the
    # repository's `< date_to` bound needs the *next* day's midnight.
    from_dt = datetime.combine(date_from, time.min) if date_from else None
    to_dt = datetime.combine(date_to + timedelta(days=1), time.min) if date_to else None

    if current_user.role == "patient":
        patient = await patient_repo.get_by_user_id(current_user.id)
        return await repo.list_filtered(
            patient_id=patient.id if patient else -1, status=status, date_from=from_dt, date_to=to_dt
        )
    return await repo.list_filtered(
        patient_id=patient_id, doctor_id=doctor_id, status=status, date_from=from_dt, date_to=to_dt
    )


@router.get("/{appointment_id}/pdf")
async def download_appointment_receipt_pdf(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    repo: AppointmentRepository = Depends(get_appointment_repository),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    appointment = await repo.get(appointment_id)
    if not appointment:
        raise NotFoundError("Appointment not found")

    if current_user.role == "patient":
        patient = await patient_repo.get_by_user_id(current_user.id)
        if not patient or appointment.patient_id != patient.id:
            raise ForbiddenError("Not authorized to view this appointment")
    elif current_user.role == "doctor":
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        if not doctor or appointment.doctor_id != doctor.id:
            raise ForbiddenError("Not authorized to view this appointment")

    patient = await patient_repo.get(appointment.patient_id)
    doctor = await db.get(Doctor, appointment.doctor_id)

    pdf_bytes = build_appointment_receipt_pdf(
        {
            "id": appointment.id,
            "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else "",
            "reason": appointment.reason,
            "status": appointment.status,
        },
        patient.full_name if patient else "Unknown",
        doctor.full_name if doctor else "—",
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="appointment_{appointment.id}.pdf"'},
    )


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentRead,
    dependencies=[Depends(require_role("admin", "receptionist", "doctor"))],
)
async def update_appointment_status(
    appointment_id: int,
    payload: AppointmentUpdateStatus,
    background_tasks: BackgroundTasks,
    service: AppointmentService = Depends(get_appointment_service),
    notification_service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user),
):
    appointment = await service.update_status(appointment_id, payload.status, current_user.id)
    await notification_service.notify_appointment_status_changed(appointment, background_tasks)
    return appointment


@router.delete(
    "/{appointment_id}",
    status_code=204,
    dependencies=[Depends(require_role("admin", "receptionist", "doctor"))],
)
async def cancel_appointment(
    appointment_id: int,
    background_tasks: BackgroundTasks,
    service: AppointmentService = Depends(get_appointment_service),
    notification_service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user),
):
    appointment = await service.update_status(appointment_id, "Cancelled", current_user.id)
    await notification_service.notify_appointment_status_changed(appointment, background_tasks)
