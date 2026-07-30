from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError
from app.database import get_db
from app.dependencies import get_doctor_repository, get_document_service, get_patient_repository
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.repositories.staff_repository import DoctorRepository
from app.schemas.document import DocumentRead
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.document_service import DocumentService
from app.services.patient_access import doctor_patient_ids

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_ROLES = ("admin", "doctor", "nurse", "receptionist", "lab_technician", "patient")
READ_ROLES = UPLOAD_ROLES


async def _assert_can_access_patient(
    db: AsyncSession, current_user: User, patient_id: int, patient_repo: PatientRepository, doctor_repo: DoctorRepository
) -> None:
    if current_user.role == "patient":
        own_patient = await patient_repo.get_by_user_id(current_user.id)
        if patient_id != (own_patient.id if own_patient else -1):
            raise ForbiddenError("Not authorized to access this patient's documents")
    elif current_user.role == "doctor":
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        allowed_ids = await doctor_patient_ids(db, doctor.id if doctor else -1)
        if patient_id not in allowed_ids:
            raise ForbiddenError("Not authorized to access this patient's documents")
    # admin / nurse / receptionist / lab_technician can access any patient's documents.


@router.post("", response_model=DocumentRead, status_code=201, dependencies=[Depends(require_role(*UPLOAD_ROLES))])
async def upload_document(
    patient_id: int = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    await _assert_can_access_patient(db, current_user, patient_id, patient_repo, doctor_repo)
    if current_user.role == "patient" and category == "Lab Report":
        raise ForbiddenError("Patients cannot add lab reports — lab results are entered by a lab technician")
    content = await file.read()
    return await service.upload(
        patient_id, category, file.filename or "upload", file.content_type or "", content, current_user.id
    )


@router.get("", response_model=list[DocumentRead], dependencies=[Depends(require_role(*READ_ROLES))])
async def list_documents(
    patient_id: int,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    await _assert_can_access_patient(db, current_user, patient_id, patient_repo, doctor_repo)
    return await service.list_filtered(patient_id, category)


@router.get("/{document_id}/download", dependencies=[Depends(require_role(*READ_ROLES))])
async def download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    service: DocumentService = Depends(get_document_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    document = await service.get_or_404(document_id)
    await _assert_can_access_patient(db, current_user, document.patient_id, patient_repo, doctor_repo)
    content = service.read_file(document)
    return Response(
        content=content,
        media_type=document.content_type,
        headers={"Content-Disposition": f'attachment; filename="{document.original_filename}"'},
    )


@router.delete("/{document_id}", status_code=204, dependencies=[Depends(require_role(*UPLOAD_ROLES))])
async def delete_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    document = await service.get_or_404(document_id)
    is_uploader = document.uploaded_by_user_id == current_user.id
    if current_user.role != "admin" and not is_uploader:
        raise ForbiddenError("Only the uploader or an admin can delete this document")
    await service.delete(document)
