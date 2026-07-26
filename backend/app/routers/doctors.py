from datetime import datetime

from fastapi import APIRouter, Depends

from app.core.exceptions import ForbiddenError, NotFoundError
from app.dependencies import get_doctor_availability_service, get_doctor_repository
from app.models.doctor import Doctor
from app.models.user import User
from app.repositories.staff_repository import DoctorRepository
from app.schemas.doctor import (
    DoctorAvailabilityCreate,
    DoctorAvailabilityRead,
    DoctorRead,
    DoctorUpdate,
)
from app.schemas.appointment import AvailableSlotsResponse
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.doctor_availability_service import DoctorAvailabilityService

router = APIRouter(prefix="/doctors", tags=["doctors"])


async def _get_or_404(repo: DoctorRepository, doctor_id: int) -> Doctor:
    doctor = await repo.get(doctor_id)
    if not doctor:
        raise NotFoundError("Doctor not found")
    return doctor


@router.get("", response_model=list[DoctorRead])
async def list_doctors(
    search: str | None = None,
    department: str | None = None,
    specialization: str | None = None,
    repo: DoctorRepository = Depends(get_doctor_repository),
):
    return await repo.list_filtered(search, department, specialization)


@router.get("/me", response_model=DoctorRead, dependencies=[Depends(require_role("doctor"))])
async def get_my_doctor_profile(
    repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    """Lets a doctor resolve their own Doctor.id client-side — needed for
    self-service availability management (mirrors GET /patients/me)."""
    doctor = await repo.get_by_user_id(current_user.id)
    if not doctor:
        raise ForbiddenError("No doctor profile linked to this account")
    return doctor


@router.get("/{doctor_id}", response_model=DoctorRead)
async def get_doctor(doctor_id: int, repo: DoctorRepository = Depends(get_doctor_repository)):
    return await _get_or_404(repo, doctor_id)


@router.patch("/{doctor_id}", response_model=DoctorRead, dependencies=[Depends(require_role("admin"))])
async def update_doctor(doctor_id: int, payload: DoctorUpdate, repo: DoctorRepository = Depends(get_doctor_repository)):
    doctor = await _get_or_404(repo, doctor_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    await repo.commit()
    await repo.refresh(doctor)
    return doctor


@router.delete("/{doctor_id}", status_code=204, dependencies=[Depends(require_role("admin"))])
async def delete_doctor(doctor_id: int, repo: DoctorRepository = Depends(get_doctor_repository)):
    doctor = await _get_or_404(repo, doctor_id)
    await repo.delete(doctor)
    await repo.commit()


@router.get("/{doctor_id}/availability", response_model=list[DoctorAvailabilityRead])
async def list_availability(doctor_id: int, service: DoctorAvailabilityService = Depends(get_doctor_availability_service)):
    return await service.list_slots(doctor_id)


@router.post(
    "/{doctor_id}/availability",
    response_model=DoctorAvailabilityRead,
    status_code=201,
    dependencies=[Depends(require_role("admin", "doctor"))],
)
async def add_availability(
    doctor_id: int,
    payload: DoctorAvailabilityCreate,
    service: DoctorAvailabilityService = Depends(get_doctor_availability_service),
    current_user: User = Depends(get_current_user),
):
    return await service.add_slot(doctor_id, payload.day_of_week, payload.start_time, payload.end_time, current_user)


@router.delete(
    "/{doctor_id}/availability/{slot_id}",
    status_code=204,
    dependencies=[Depends(require_role("admin", "doctor"))],
)
async def remove_availability(
    doctor_id: int,
    slot_id: int,
    service: DoctorAvailabilityService = Depends(get_doctor_availability_service),
    current_user: User = Depends(get_current_user),
):
    await service.remove_slot(doctor_id, slot_id, current_user)


@router.get("/{doctor_id}/available-slots", response_model=AvailableSlotsResponse)
async def available_slots(
    doctor_id: int,
    date: str,
    service: DoctorAvailabilityService = Depends(get_doctor_availability_service),
):
    on_date = datetime.strptime(date, "%Y-%m-%d").date()
    times = await service.available_slots_on(doctor_id, on_date)
    return AvailableSlotsResponse(doctor_id=doctor_id, date=date, available_times=times)
