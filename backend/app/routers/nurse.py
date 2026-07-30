from fastapi import APIRouter, Depends, HTTPException

from app.core.exceptions import NotFoundError
from app.dependencies import get_nurse_repository, get_nurse_service, get_patient_repository
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.repositories.staff_repository import NurseRepository
from app.schemas.nurse import (
    MedicineAdministrationCreate,
    MedicineAdministrationRead,
    PatientVitalsCreate,
    PatientVitalsRead,
)
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.nurse_service import NurseService

router = APIRouter(tags=["nurse"])

READ_ROLES = ("admin", "doctor", "nurse", "patient")


async def _current_nurse_id(nurse_repo: NurseRepository, current_user: User) -> int:
    nurse = await nurse_repo.get_by_user_id(current_user.id)
    if not nurse:
        raise HTTPException(status_code=403, detail="No nurse profile linked to this account")
    return nurse.id


@router.post("/patient-vitals", response_model=PatientVitalsRead, dependencies=[Depends(require_role("nurse"))])
async def record_vitals(
    payload: PatientVitalsCreate,
    service: NurseService = Depends(get_nurse_service),
    nurse_repo: NurseRepository = Depends(get_nurse_repository),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    current_user: User = Depends(get_current_user),
):
    nurse_id = await _current_nurse_id(nurse_repo, current_user)
    if not await patient_repo.get(payload.patient_id):
        raise NotFoundError("Patient not found")
    data = payload.model_dump(exclude={"patient_id"})
    return await service.record_vitals(payload.patient_id, nurse_id, **data)


@router.get("/patient-vitals", response_model=list[PatientVitalsRead], dependencies=[Depends(require_role(*READ_ROLES))])
async def list_vitals(
    patient_id: int | None = None,
    service: NurseService = Depends(get_nurse_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "patient":
        patient = await patient_repo.get_by_user_id(current_user.id)
        return await service.list_vitals(patient.id if patient else -1)
    if patient_id is None:
        raise HTTPException(status_code=422, detail="patient_id is required")
    return await service.list_vitals(patient_id)


@router.post(
    "/medicine-administration",
    response_model=MedicineAdministrationRead,
    dependencies=[Depends(require_role("nurse"))],
)
async def record_administration(
    payload: MedicineAdministrationCreate,
    service: NurseService = Depends(get_nurse_service),
    nurse_repo: NurseRepository = Depends(get_nurse_repository),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    current_user: User = Depends(get_current_user),
):
    nurse_id = await _current_nurse_id(nurse_repo, current_user)
    if not await patient_repo.get(payload.patient_id):
        raise NotFoundError("Patient not found")
    return await service.record_administration(payload.patient_id, nurse_id, payload.medicine, payload.dose)


@router.get(
    "/medicine-administration",
    response_model=list[MedicineAdministrationRead],
    dependencies=[Depends(require_role(*READ_ROLES))],
)
async def list_administrations(
    patient_id: int | None = None,
    service: NurseService = Depends(get_nurse_service),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "patient":
        patient = await patient_repo.get_by_user_id(current_user.id)
        return await service.list_administrations(patient.id if patient else -1)
    if patient_id is None:
        raise HTTPException(status_code=422, detail="patient_id is required")
    return await service.list_administrations(patient_id)
