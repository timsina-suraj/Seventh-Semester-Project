import json

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.database import get_db
from app.dependencies import get_doctor_repository, get_patient_repository, get_registration_service
from app.models.patient import Patient
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.repositories.staff_repository import DoctorRepository
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.patient_access import doctor_patient_ids
from app.services.registration_service import RegistrationService

router = APIRouter(prefix="/patients", tags=["patients"])


def _to_read(patient: Patient) -> PatientRead:
    linked_user = patient.user
    address = {}
    if patient.encrypted_address:
        try:
            address = json.loads(patient.encrypted_address)
        except (TypeError, ValueError):
            address = {}
    return PatientRead(
        id=patient.id,
        patient_number=patient.patient_number,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        blood_group=patient.blood_group,
        phone=patient.encrypted_phone,
        district=patient.district,
        province=address.get("province"),
        municipality=address.get("municipality"),
        emergency_contact=patient.encrypted_emergency_contact,
        allergies=patient.allergies,
        created_at=patient.created_at,
        login_email=linked_user.email if linked_user else None,
        must_change_password=linked_user.must_change_password if linked_user else None,
    )


async def _get_or_404(repo: PatientRepository, patient_id: int) -> Patient:
    patient = await repo.get(patient_id)
    if not patient:
        raise NotFoundError("Patient not found")
    return patient


@router.post("", response_model=PatientRead, dependencies=[Depends(require_role("admin", "receptionist"))])
async def create_patient(
    payload: PatientCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    service: RegistrationService = Depends(get_registration_service),
    repo: PatientRepository = Depends(get_patient_repository),
    current_user: User = Depends(get_current_user),
):
    ip = request.client.host if request.client else None
    patient = await service.create_patient(payload, actor_user_id=current_user.id, background_tasks=background_tasks, ip_address=ip)
    # Re-fetch with `user` eager-loaded (registration_service's session
    # object may not have it populated for lazy access under async SQLAlchemy).
    patient = await repo.get(patient.id)
    return _to_read(patient)


@router.get("", response_model=list[PatientRead], dependencies=[Depends(require_role("admin", "doctor", "nurse", "receptionist"))])
async def list_patients(
    district: str | None = None,
    search: str | None = None,
    blood_group: str | None = None,
    db: AsyncSession = Depends(get_db),
    repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    patients = await repo.list_filtered(district, search, blood_group)

    if current_user.role == "doctor":
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        allowed_ids = await doctor_patient_ids(db, doctor.id if doctor else -1)
        patients = [p for p in patients if p.id in allowed_ids]

    return [_to_read(p) for p in patients]


@router.get("/me", response_model=PatientRead)
async def get_my_patient_record(
    repo: PatientRepository = Depends(get_patient_repository),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "patient":
        raise ForbiddenError("Only patient accounts have a linked patient record")
    patient = await repo.get_by_user_id(current_user.id)
    if not patient:
        raise NotFoundError("No patient record is linked to this account yet")
    return _to_read(patient)


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    patient = await _get_or_404(repo, patient_id)
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise ForbiddenError("Not authorized to view this patient")

    if current_user.role == "doctor":
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        allowed_ids = await doctor_patient_ids(db, doctor.id if doctor else -1)
        if patient_id not in allowed_ids:
            raise ForbiddenError("Not authorized to view this patient")

    return _to_read(patient)


@router.patch("/{patient_id}", response_model=PatientRead, dependencies=[Depends(require_role("admin", "receptionist"))])
async def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    repo: PatientRepository = Depends(get_patient_repository),
):
    patient = await _get_or_404(repo, patient_id)
    data = payload.model_dump(exclude_unset=True)

    if "phone" in data:
        patient.encrypted_phone = data.pop("phone")
    if "emergency_contact" in data:
        patient.encrypted_emergency_contact = data.pop("emergency_contact")
    if "province" in data or "municipality" in data:
        try:
            address = json.loads(patient.encrypted_address) if patient.encrypted_address else {}
        except (TypeError, ValueError):
            address = {}
        if "province" in data:
            address["province"] = data.pop("province")
        if "municipality" in data:
            address["municipality"] = data.pop("municipality")
        patient.encrypted_address = json.dumps(address)

    for field in ("full_name", "date_of_birth", "gender", "blood_group", "district", "allergies"):
        if field in data:
            setattr(patient, field, data[field])

    await repo.commit()
    await repo.refresh(patient)
    return _to_read(patient)


@router.delete("/{patient_id}", status_code=204, dependencies=[Depends(require_role("admin"))])
async def delete_patient(patient_id: int, repo: PatientRepository = Depends(get_patient_repository)):
    patient = await _get_or_404(repo, patient_id)
    await repo.delete(patient)
    await repo.commit()
