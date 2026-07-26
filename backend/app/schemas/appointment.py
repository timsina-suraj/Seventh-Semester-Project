from datetime import datetime, time

from pydantic import BaseModel, field_validator

from app.models.appointment import VALID_STATUSES


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    reason: str | None = None


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
