"""Read/Update schemas for the three staff profile tables that don't have
their own dedicated resource router (Doctor already does — see
schemas/doctor.py). Nurse/Receptionist/LabTechnician accounts are created
via POST /auth/register (StaffCreate); these are for admin edits to an
existing roster row only, mirroring DoctorUpdate/DoctorRead exactly --
including that every Optional field, if provided, still has to satisfy the
same non-empty/length bounds its column declares (see DoctorUpdate's
docstring for why that isn't automatic just because a field is Optional)."""
from pydantic import BaseModel, Field


class NurseUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=128)
    department: str | None = Field(default=None, min_length=1, max_length=128)
    shift: str | None = Field(default=None, min_length=1, max_length=20)


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
    full_name: str | None = Field(default=None, min_length=1, max_length=128)


class ReceptionistRead(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: str

    class Config:
        from_attributes = True


class LabTechnicianUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=128)
    department: str | None = Field(default=None, min_length=1, max_length=128)


class LabTechnicianRead(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: str
    department: str

    class Config:
        from_attributes = True
