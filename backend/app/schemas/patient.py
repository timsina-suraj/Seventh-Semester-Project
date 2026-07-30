from datetime import date, datetime, timedelta

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.nepal_locations import VALID_DISTRICTS, VALID_PROVINCES
from app.models.patient import VALID_BLOOD_GROUPS, VALID_GENDERS

# Plausibility guard, not a medical claim -- just rules out fat-fingered
# years (typo'd century, a DOB entered in the future, etc.).
_MAX_PLAUSIBLE_AGE_YEARS = 120


def _validate_phone(v: str | None) -> str | None:
    if v is None or v == "":
        return v
    digits = v.replace("+", "").replace(" ", "").replace("-", "")
    if not digits.isdigit() or not (7 <= len(digits) <= 15):
        raise ValueError("phone must contain 7-15 digits")
    return v


def _validate_district(v: str | None) -> str | None:
    if v is None or v == "":
        return v
    if v not in VALID_DISTRICTS:
        raise ValueError("district must be one of Nepal's 77 official districts")
    return v


def _validate_province(v: str | None) -> str | None:
    if v is None or v == "":
        return v
    if v not in VALID_PROVINCES:
        raise ValueError(f"province must be one of {VALID_PROVINCES}")
    return v


def _validate_gender(v: str | None) -> str | None:
    if v is None:
        return v
    if v not in VALID_GENDERS:
        raise ValueError(f"gender must be one of {VALID_GENDERS}")
    return v


def _validate_blood_group(v: str | None) -> str | None:
    if v is None:
        return v
    if v not in VALID_BLOOD_GROUPS:
        raise ValueError(f"blood_group must be one of {VALID_BLOOD_GROUPS}")
    return v


def _validate_date_of_birth(v: date | None) -> date | None:
    if v is None:
        return v
    today = date.today()
    if v > today:
        raise ValueError("date_of_birth cannot be in the future")
    # timedelta (not date(year - N, ...)) so a Feb 29 today doesn't blow up
    # on a target year that isn't a leap year.
    oldest_plausible = today - timedelta(days=_MAX_PLAUSIBLE_AGE_YEARS * 365.25)
    if v < oldest_plausible:
        raise ValueError(f"date_of_birth cannot be more than {_MAX_PLAUSIBLE_AGE_YEARS} years ago")
    return v


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    date_of_birth: date
    gender: str
    blood_group: str = "Unknown"

    phone: str | None = None
    # Address is stored as: district (plain, queryable — required by the
    # dengue ML feature pipeline) + province/municipality (encrypted, packed
    # together as a JSON blob into a single EncryptedString(512) column --
    # the max_length below leaves margin for both fields plus the JSON
    # object's own syntax to still fit under that ciphertext budget).
    district: str = Field(min_length=1)
    province: str | None = None
    municipality: str | None = Field(default=None, max_length=128)
    emergency_contact: str | None = None
    allergies: str | None = Field(default=None, max_length=1000)

    # The patient's login. There's no separate "username" field -- the
    # email itself is used as the username, so the receptionist only has to
    # type it once, and the patient only has to remember one thing.
    email: EmailStr

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        return _validate_gender(v)

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: str) -> str:
        return _validate_blood_group(v)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        return _validate_phone(v)

    @field_validator("emergency_contact")
    @classmethod
    def validate_emergency_contact(cls, v: str | None) -> str | None:
        return _validate_phone(v)

    @field_validator("district")
    @classmethod
    def validate_district(cls, v: str) -> str:
        return _validate_district(v)

    @field_validator("province")
    @classmethod
    def validate_province(cls, v: str | None) -> str | None:
        return _validate_province(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        return _validate_date_of_birth(v)


class PatientUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    phone: str | None = None
    district: str | None = None
    province: str | None = None
    municipality: str | None = Field(default=None, max_length=128)
    emergency_contact: str | None = None
    allergies: str | None = Field(default=None, max_length=1000)

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str | None) -> str | None:
        return _validate_gender(v)

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: str | None) -> str | None:
        return _validate_blood_group(v)

    @field_validator("district")
    @classmethod
    def validate_district(cls, v: str | None) -> str | None:
        return _validate_district(v)

    @field_validator("province")
    @classmethod
    def validate_province(cls, v: str | None) -> str | None:
        return _validate_province(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date | None) -> date | None:
        return _validate_date_of_birth(v)


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
