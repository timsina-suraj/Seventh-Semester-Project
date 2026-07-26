"""Admin edits to existing Nurse/Receptionist/LabTechnician roster rows —
mirrors doctors.py's GET/PATCH pattern exactly (Doctor already has its own
router; these three share an identical shape so they're grouped here rather
than in three near-empty files)."""
from fastapi import APIRouter, Depends

from app.core.exceptions import NotFoundError
from app.dependencies import get_lab_technician_repository, get_nurse_repository, get_receptionist_repository
from app.repositories.staff_repository import LabTechnicianRepository, NurseRepository, ReceptionistRepository
from app.schemas.staff import (
    LabTechnicianRead,
    LabTechnicianUpdate,
    NurseRead,
    NurseUpdate,
    ReceptionistRead,
    ReceptionistUpdate,
)
from app.security.rbac import require_role

router = APIRouter(dependencies=[Depends(require_role("admin"))])


async def _get_or_404(repo, id_: int):
    obj = await repo.get(id_)
    if not obj:
        raise NotFoundError("Not found")
    return obj


@router.get("/nurses", response_model=list[NurseRead])
async def list_nurses(repo: NurseRepository = Depends(get_nurse_repository)):
    return await repo.list()


@router.patch("/nurses/{nurse_id}", response_model=NurseRead)
async def update_nurse(nurse_id: int, payload: NurseUpdate, repo: NurseRepository = Depends(get_nurse_repository)):
    nurse = await _get_or_404(repo, nurse_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(nurse, field, value)
    await repo.commit()
    await repo.refresh(nurse)
    return nurse


@router.get("/receptionists", response_model=list[ReceptionistRead])
async def list_receptionists(repo: ReceptionistRepository = Depends(get_receptionist_repository)):
    return await repo.list()


@router.patch("/receptionists/{receptionist_id}", response_model=ReceptionistRead)
async def update_receptionist(
    receptionist_id: int, payload: ReceptionistUpdate, repo: ReceptionistRepository = Depends(get_receptionist_repository)
):
    receptionist = await _get_or_404(repo, receptionist_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(receptionist, field, value)
    await repo.commit()
    await repo.refresh(receptionist)
    return receptionist


@router.get("/lab-technicians", response_model=list[LabTechnicianRead])
async def list_lab_technicians(repo: LabTechnicianRepository = Depends(get_lab_technician_repository)):
    return await repo.list()


@router.patch("/lab-technicians/{lab_technician_id}", response_model=LabTechnicianRead)
async def update_lab_technician(
    lab_technician_id: int, payload: LabTechnicianUpdate, repo: LabTechnicianRepository = Depends(get_lab_technician_repository)
):
    lab_technician = await _get_or_404(repo, lab_technician_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lab_technician, field, value)
    await repo.commit()
    await repo.refresh(lab_technician)
    return lab_technician
