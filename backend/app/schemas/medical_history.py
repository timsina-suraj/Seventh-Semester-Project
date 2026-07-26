from datetime import date

from pydantic import BaseModel, field_validator

from app.models.patient_conditions import VALID_CONDITION_STATUSES


class MedicalHistoryCreate(BaseModel):
    patient_id: int
    condition_name: str
    diagnosed_date: date | None = None
    notes: str | None = None


class MedicalHistoryRead(BaseModel):
    id: int
    patient_id: int
    condition_name: str
    diagnosed_date: date | None
    notes: str | None

    class Config:
        from_attributes = True


class PatientConditionCreate(BaseModel):
    patient_id: int
    condition: str
    status: str = "Active"
    diagnosed_date: date | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_CONDITION_STATUSES:
            raise ValueError(f"status must be one of {VALID_CONDITION_STATUSES}")
        return v


class PatientConditionRead(BaseModel):
    id: int
    patient_id: int
    condition: str
    status: str
    diagnosed_date: date | None

    class Config:
        from_attributes = True
