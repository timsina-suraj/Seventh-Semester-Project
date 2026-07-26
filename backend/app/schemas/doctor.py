from datetime import time

from pydantic import BaseModel, Field, field_validator


class DoctorUpdate(BaseModel):
    """Doctor accounts are created via POST /auth/register (StaffCreate) so
    the login and the roster row are always created together. This is for
    admin edits to an existing doctor's roster info only."""

    full_name: str | None = None
    department: str | None = None
    specialization: str | None = None
    license_number: str | None = None


class DoctorRead(BaseModel):
    id: int
    user_id: int
    employee_id: str
    full_name: str
    department: str
    specialization: str
    license_number: str

    class Config:
        from_attributes = True


class DoctorAvailabilityCreate(BaseModel):
    day_of_week: int = Field(ge=0, le=6)  # 0=Monday .. 6=Sunday
    start_time: time
    end_time: time

    @field_validator("end_time")
    @classmethod
    def validate_range(cls, v: time, info) -> time:
        start = info.data.get("start_time")
        if start is not None and v <= start:
            raise ValueError("end_time must be after start_time")
        return v


class DoctorAvailabilityRead(BaseModel):
    id: int
    doctor_id: int
    day_of_week: int
    start_time: time
    end_time: time

    class Config:
        from_attributes = True
