from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.patient import VALID_BLOOD_GROUPS, VALID_GENDERS


def _validate_phone(v: str | None) -> str | None:
    if v is None or v == "":
        return v
    digits = v.replace("+", "").replace(" ", "").replace("-", "")
    if not digits.isdigit() or not (7 <= len(digits) <= 15):
        raise ValueError("phone must contain 7-15 digits")
    return v


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    date_of_birth: date
    gender: str
    blood_group: str = "Unknown"

    phone: str | None = None
    # Address is stored as: district (plain, queryable — required by the
    # dengue ML feature pipeline) + province/municipality (encrypted).
    district: str = Field(min_length=1)
    province: str | None = None
    municipality: str | None = None
    emergency_contact: str | None = None
    allergies: str | None = None

    # The patient's login. There's no separate "username" field -- the
    # email itself is used as the username, so the receptionist only has to
    # type it once, and the patient only has to remember one thing.
    email: EmailStr

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v not in VALID_GENDERS:
            raise ValueError(f"gender must be one of {VALID_GENDERS}")
        return v

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: str) -> str:
        if v not in VALID_BLOOD_GROUPS:
            raise ValueError(f"blood_group must be one of {VALID_BLOOD_GROUPS}")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        return _validate_phone(v)

    @field_validator("emergency_contact")
    @classmethod
    def validate_emergency_contact(cls, v: str | None) -> str | None:
        return _validate_phone(v)


class PatientUpdate(BaseModel):
    full_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    phone: str | None = None
    district: str | None = None
    province: str | None = None
    municipality: str | None = None
    emergency_contact: str | None = None
    allergies: str | None = None


class PatientRead(BaseModel):
    id: int
    patient_number: str
    full_name: str
    date_of_birth: date
    gender: str
    blood_group: str
    phone: str | None
    district: str
    province: str | None
    municipality: str | None
    emergency_contact: str | None
    allergies: str | None
    created_at: datetime
    login_email: str | None = None
    must_change_password: bool | None = None

    class Config:
        from_attributes = True
