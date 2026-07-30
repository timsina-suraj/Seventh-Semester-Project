"""Structured chronic/past-condition tracking (Module 8's replacement for
the old free-text medical_history/clinical_history blobs, doubling as
supporting tables for Module 17's comorbidity features)."""
from fastapi import APIRouter, Depends

from app.core.exceptions import NotFoundError
from app.dependencies import get_medical_history_repository, get_patient_condition_repository, get_patient_repository
from app.models.medical_history import MedicalHistory
from app.models.patient_conditions import PatientCondition
from app.repositories.medical_history_repository import MedicalHistoryRepository, PatientConditionRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.medical_history import (
    MedicalHistoryCreate,
    MedicalHistoryRead,
    PatientConditionCreate,
    PatientConditionRead,
)
from app.security.rbac import require_role

router = APIRouter(tags=["patient-history"])

READ_ROLES = ("admin", "doctor", "nurse", "patient")
WRITE_ROLES = ("admin", "doctor")


@router.post("/medical-history", response_model=MedicalHistoryRead, dependencies=[Depends(require_role(*WRITE_ROLES))])
async def add_medical_history(
    payload: MedicalHistoryCreate,
    repo: MedicalHistoryRepository = Depends(get_medical_history_repository),
    patient_repo: PatientRepository = Depends(get_patient_repository),
):
    if not await patient_repo.get(payload.patient_id):
        raise NotFoundError("Patient not found")
    entry = MedicalHistory(**payload.model_dump())
    repo.add(entry)
    await repo.commit()
    await repo.refresh(entry)
    return entry


@router.get("/medical-history", response_model=list[MedicalHistoryRead], dependencies=[Depends(require_role(*READ_ROLES))])
async def list_medical_history(patient_id: int, repo: MedicalHistoryRepository = Depends(get_medical_history_repository)):
    return await repo.list_for_patient(patient_id)


@router.post(
    "/patient-conditions", response_model=PatientConditionRead, dependencies=[Depends(require_role(*WRITE_ROLES))]
)
async def add_patient_condition(
    payload: PatientConditionCreate,
    repo: PatientConditionRepository = Depends(get_patient_condition_repository),
    patient_repo: PatientRepository = Depends(get_patient_repository),
):
    if not await patient_repo.get(payload.patient_id):
        raise NotFoundError("Patient not found")
    entry = PatientCondition(**payload.model_dump())
    repo.add(entry)
    await repo.commit()
    await repo.refresh(entry)
    return entry


@router.get(
    "/patient-conditions", response_model=list[PatientConditionRead], dependencies=[Depends(require_role(*READ_ROLES))]
)
async def list_patient_conditions(patient_id: int, repo: PatientConditionRepository = Depends(get_patient_condition_repository)):
    return await repo.list_for_patient(patient_id)
