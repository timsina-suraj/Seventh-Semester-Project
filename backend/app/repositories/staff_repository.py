"""Repositories for the four employee_id-bearing staff profile tables
(Doctor, Nurse, Receptionist, LabTechnician) — they share an identical
`user_id` + `employee_id` shape, so the sequence-number generation lives
once on a shared base. Admin has no employee_id (per spec) and, since
admin accounts are bootstrap-only (see registration_service.create_admin)
rather than managed through a roster UI like the other four roles, has no
repository of its own here."""
from sqlalchemy import func, select

from app.models.doctor import Doctor
from app.models.lab_technician import LabTechnician
from app.models.nurse import Nurse
from app.models.receptionist import Receptionist
from app.repositories.base import BaseRepository, ModelT


class StaffProfileRepository(BaseRepository[ModelT]):
    employee_id_prefix: str

    async def get_by_user_id(self, user_id: int) -> ModelT | None:
        return await self.get_by(user_id=user_id)

    async def next_employee_id(self) -> str:
        count = await self.db.scalar(select(func.count()).select_from(self.model))
        return f"{self.employee_id_prefix}-{(count or 0) + 1:04d}"


class DoctorRepository(StaffProfileRepository[Doctor]):
    model = Doctor
    employee_id_prefix = "DOC"

    async def list_filtered(
        self, search: str | None = None, department: str | None = None, specialization: str | None = None
    ) -> list[Doctor]:
        stmt = select(Doctor)
        if search:
            stmt = stmt.where(Doctor.full_name.ilike(f"%{search}%"))
        if department:
            stmt = stmt.where(Doctor.department == department)
        if specialization:
            stmt = stmt.where(Doctor.specialization == specialization)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class NurseRepository(StaffProfileRepository[Nurse]):
    model = Nurse
    employee_id_prefix = "NUR"


class ReceptionistRepository(StaffProfileRepository[Receptionist]):
    model = Receptionist
    employee_id_prefix = "REC"


class LabTechnicianRepository(StaffProfileRepository[LabTechnician]):
    model = LabTechnician
    employee_id_prefix = "LAB"
