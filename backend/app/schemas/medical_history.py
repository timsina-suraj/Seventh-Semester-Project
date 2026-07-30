from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.models.patient_conditions import VALID_CONDITION_STATUSES

# condition_name is EncryptedString(256), notes is EncryptedString(1024) --
# see medical_record.py's comment for why these are plaintext caps well under
# the column's own number, not equal to it (that number is a ciphertext budget).
_CONDITION_NAME_MAX = 150
_NOTES_MAX = 700


def _validate_not_future(v: date | None) -> date | None:
    if v is not None and v > date.today():
        raise ValueError("diagnosed_date cannot be in the future")
    return v


class MedicalHistoryCreate(BaseModel):
    patient_id: int
    condition_name: str = Field(min_length=1, max_length=_CONDITION_NAME_MAX)
    diagnosed_date: date | None = None
    notes: str | None = Field(default=None, max_length=_NOTES_MAX)

    @field_validator("diagnosed_date")
    @classmethod
    def validate_diagnosed_date(cls, v: date | None) -> date | None:
        return _validate_not_future(v)


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
    condition: str = Field(min_length=1, max_length=128)  # plain String(128), not encrypted
    status: str = "Active"
    diagnosed_date: date | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_CONDITION_STATUSES:
            raise ValueError(f"status must be one of {VALID_CONDITION_STATUSES}")
        return v

    @field_validator("diagnosed_date")
    @classmethod
    def validate_diagnosed_date(cls, v: date | None) -> date | None:
        return _validate_not_future(v)


class PatientConditionRead(BaseModel):
    id: int
    patient_id: int
    condition: str
    status: str
    diagnosed_date: date | None

    class Config:
        from_attributes = True
