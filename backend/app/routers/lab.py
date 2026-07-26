from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.database import get_db
from app.dependencies import get_doctor_repository, get_lab_service, get_notification_service, get_patient_repository
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.repositories.staff_repository import DoctorRepository
from app.schemas.lab import LabResultUpload, LabTestCreate, LabTestRead
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.lab_service import LabService
from app.services.notification_service import NotificationService
from app.services.patient_access import doctor_patient_ids
from app.services.pdf_service import build_lab_report_pdf

router = APIRouter(prefix="/lab-tests", tags=["lab"])

READ_ROLES = ("admin", "doctor", "nurse", "patient", "lab_technician")


@router.post("", response_model=LabTestRead, dependencies=[Depends(require_role("doctor"))])
async def request_lab_test(
    payload: LabTestCreate,
    service: LabService = Depends(get_lab_service),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    doctor = await doctor_repo.get_by_user_id(current_user.id)
    if not doctor:
        raise ForbiddenError("No doctor profile linked to this account")
    return await service.request_test(payload.patient_id, doctor.id, payload.test_name, current_user.id)


@router.get("", response_model=list[LabTestRead], dependencies=[Depends(require_role(*READ_ROLES))])
async def list_lab_tests(
    service: LabService = Depends(get_lab_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    current_user: User = Depends(get_current_user),
    patient_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
):
    if current_user.role == "patient":
        patient = await patient_repo.get_by_user_id(current_user.id)
        return await service.list_filtered(patient_id=patient.id if patient else -1, status=status, search=search)
    return await service.list_filtered(patient_id=patient_id, status=status, search=search)


@router.post(
    "/{lab_test_id}/result",
    response_model=LabTestRead,
    dependencies=[Depends(require_role("lab_technician", "admin"))],
)
async def upload_lab_result(
    lab_test_id: int,
    payload: LabResultUpload,
    background_tasks: BackgroundTasks,
    service: LabService = Depends(get_lab_service),
    notification_service: NotificationService = Depends(get_notification_service),
    current_user: User = Depends(get_current_user),
):
    lab_test = await service.upload_result(lab_test_id, payload.result_value, payload.result_file, current_user.id)
    await notification_service.notify_lab_result_ready(lab_test, background_tasks)
    return lab_test


@router.get("/{lab_test_id}/pdf", dependencies=[Depends(require_role(*READ_ROLES))])
async def download_lab_report_pdf(
    lab_test_id: int,
    db: AsyncSession = Depends(get_db),
    service: LabService = Depends(get_lab_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    lab_test = await service.get_with_result(lab_test_id)
    if not lab_test:
        raise NotFoundError("Lab test not found")
    patient = await patient_repo.get(lab_test.patient_id)

    if current_user.role == "patient" and (not patient or patient.user_id != current_user.id):
        raise ForbiddenError("Not authorized to view this lab test")
    if current_user.role == "doctor":
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        allowed_ids = await doctor_patient_ids(db, doctor.id if doctor else -1)
        if lab_test.patient_id not in allowed_ids:
            raise ForbiddenError("Not authorized to view this lab test")

    pdf_bytes = build_lab_report_pdf(
        {
            "id": lab_test.id,
            "test_name": lab_test.test_name,
            "status": lab_test.status,
            "requested_at": lab_test.requested_at.isoformat() if lab_test.requested_at else "",
            "result": (
                {
                    "result_value": lab_test.result.result_value,
                    "completed_at": lab_test.result.completed_at.isoformat() if lab_test.result.completed_at else None,
                }
                if lab_test.result
                else None
            ),
        },
        patient.full_name if patient else "Unknown",
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="lab_report_{lab_test.id}.pdf"'},
    )
