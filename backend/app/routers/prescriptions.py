from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.database import get_db
from app.dependencies import get_doctor_repository, get_notification_service, get_patient_repository, get_prescription_service
from app.models.doctor import Doctor
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.repositories.staff_repository import DoctorRepository
from app.schemas.prescription import PrescriptionCreate, PrescriptionRead
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.notification_service import NotificationService
from app.services.patient_access import doctor_patient_ids
from app.services.pdf_service import build_prescription_pdf
from app.services.prescription_service import PrescriptionService

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

READ_ROLES = ("admin", "doctor", "nurse", "patient")


@router.post("", response_model=PrescriptionRead, dependencies=[Depends(require_role("doctor"))])
async def create_prescription(
    payload: PrescriptionCreate,
    background_tasks: BackgroundTasks,
    service: PrescriptionService = Depends(get_prescription_service),
    notification_service: NotificationService = Depends(get_notification_service),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    doctor = await doctor_repo.get_by_user_id(current_user.id)
    if not doctor:
        raise ForbiddenError("No doctor profile linked to this account")
    prescription = await service.create_with_items(
        payload.patient_id,
        doctor.id,
        payload.medical_record_id,
        [item.model_dump() for item in payload.items],
        current_user.id,
    )
    await notification_service.notify_prescription_created(prescription, doctor.full_name, background_tasks)
    return prescription


@router.get("", response_model=list[PrescriptionRead], dependencies=[Depends(require_role(*READ_ROLES))])
async def list_prescriptions(
    db: AsyncSession = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
    patient_id: int | None = None,
):
    if current_user.role == "patient":
        patient = await patient_repo.get_by_user_id(current_user.id)
        return await service.list_filtered(patient_id=patient.id if patient else -1)
    if current_user.role == "doctor":
        # A doctor sees only their own patients' prescriptions — matches the
        # scoping already enforced on the single-prescription PDF endpoint
        # below and on medical-records' doctor-scoped list.
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        allowed_ids = await doctor_patient_ids(db, doctor.id if doctor else -1)
        if patient_id is not None and patient_id not in allowed_ids:
            return []
        prescriptions = await service.list_filtered(patient_id=patient_id)
        return [p for p in prescriptions if p.patient_id in allowed_ids]
    return await service.list_filtered(patient_id=patient_id)


@router.get("/{prescription_id}/pdf", dependencies=[Depends(require_role(*READ_ROLES))])
async def download_prescription_pdf(
    prescription_id: int,
    db: AsyncSession = Depends(get_db),
    service: PrescriptionService = Depends(get_prescription_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    prescription = await service.get_with_items(prescription_id)
    if not prescription:
        raise NotFoundError("Prescription not found")
    patient = await patient_repo.get(prescription.patient_id)

    if current_user.role == "patient" and (not patient or patient.user_id != current_user.id):
        raise ForbiddenError("Not authorized to view this prescription")
    if current_user.role == "doctor":
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        allowed_ids = await doctor_patient_ids(db, doctor.id if doctor else -1)
        if prescription.patient_id not in allowed_ids:
            raise ForbiddenError("Not authorized to view this prescription")

    prescribing_doctor = await db.get(Doctor, prescription.doctor_id)
    pdf_bytes = build_prescription_pdf(
        {
            "id": prescription.id,
            "created_at": prescription.created_at.isoformat() if prescription.created_at else "",
            "items": [
                {
                    "medicine_name": item.medicine_name, "quantity": item.quantity, "dosage": item.dosage,
                    "frequency": item.frequency, "duration": item.duration, "instructions": item.instructions,
                }
                for item in prescription.items
            ],
        },
        patient.full_name if patient else "Unknown",
        prescribing_doctor.full_name if prescribing_doctor else "—",
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="prescription_{prescription.id}.pdf"'},
    )
