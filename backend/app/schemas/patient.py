from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str | None = None
    phone: str | None = None
    age: int = Field(ge=0, le=120)
    gender: str
    district: str

    # The patient's login. There's no separate "username" field -- the
    # email itself is used as the username, so admin/receptionist only
    # have to type it once, and the patient only has to remember one thing.
    email: EmailStr

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        allowed = {"Male", "Female", "Other"}
        if v not in allowed:
            raise ValueError(f"gender must be one of {allowed}")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        digits = v.replace("+", "").replace(" ", "").replace("-", "")
        if not digits.isdigit() or not (7 <= len(digits) <= 15):
            raise ValueError("phone must contain 7-15 digits")
        return v


class PatientUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = None
    district: str | None = None


class PatientRead(BaseModel):
    id: int
    name: str
    address: str | None
    phone: str | None
    age: int
    gender: str
    district: str
    created_date: datetime
    login_email: str | None = None
    must_change_password: bool | None = None

    class Config:
        from_attributes = True


class PatientCreated(PatientRead):
    """Returned once, right after registration, so the admin/receptionist
    can hand the one-time password to the patient. Never returned again."""

    temporary_password: str