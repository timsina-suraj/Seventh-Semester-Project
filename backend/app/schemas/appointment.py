from datetime import datetime, time

from pydantic import BaseModel, Field, field_validator

from app.models.appointment import VALID_STATUSES


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    # DB column is Text (no declared limit at all) -- this app-level cap
    # exists specifically because "no limit" is itself the defect, not
    # because it needs to match some existing DB-side number.
    reason: str | None = Field(default=None, max_length=500)


class AppointmentUpdateStatus(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v


class AppointmentRead(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    reason: str | None
    status: str
    created_date: datetime

    class Config:
        from_attributes = True


class AvailableSlotsResponse(BaseModel):
    doctor_id: int
    date: str
    available_times: list[time]
