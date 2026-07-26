"""Read/Update schemas for the three staff profile tables that don't have
their own dedicated resource router (Doctor already does — see
schemas/doctor.py). Nurse/Receptionist/LabTechnician accounts are created
via POST /auth/register (StaffCreate); these are for admin edits to an
existing roster row only, mirroring DoctorUpdate/DoctorRead exactly."""
from pydantic import BaseModel


class NurseUpdate(BaseModel):
    full_name: str | None = None
    department: str | None = None
    shift: str | None = None


class NurseRead(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: str
    department: str
    shift: str

    class Config:
        from_attributes = True


class ReceptionistUpdate(BaseModel):
    full_name: str | None = None


class ReceptionistRead(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: str

    class Config:
        from_attributes = True


class LabTechnicianUpdate(BaseModel):
    full_name: str | None = None
    department: str | None = None


class LabTechnicianRead(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: str
    department: str

    class Config:
        from_attributes = True
