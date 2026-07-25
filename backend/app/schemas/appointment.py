from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.appointment import VALID_STATUSES


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    scheduled_at: datetime
    reason: str | None = None


class AppointmentUpdate(BaseModel):
    scheduled_at: datetime | None = None
    reason: str | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v


class AppointmentRead(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    scheduled_at: datetime
    reason: str | None
    status: str
    created_date: datetime

    class Config:
        from_attributes = True
