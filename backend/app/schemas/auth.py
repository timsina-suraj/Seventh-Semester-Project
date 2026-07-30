import re

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.user import VALID_STAFF_ROLES

_PASSWORD_LOWER = re.compile(r"[a-z]")
_PASSWORD_UPPER = re.compile(r"[A-Z]")
_PASSWORD_DIGIT = re.compile(r"[0-9]")
_PASSWORD_SPECIAL = re.compile(r"[^A-Za-z0-9]")


def _validate_password_strength(v: str) -> str:
    """Requires at least one lowercase letter, one uppercase letter, one
    digit, and one special (non-alphanumeric) character, on top of the
    8-128 length constraint already enforced by each field's Field(...).
    Reports every rule the password fails, not just the first one, so the
    caller gets one actionable error instead of having to resubmit
    repeatedly to discover each missing requirement in turn."""
    missing = []
    if not _PASSWORD_LOWER.search(v):
        missing.append("a lowercase letter")
    if not _PASSWORD_UPPER.search(v):
        missing.append("an uppercase letter")
    if not _PASSWORD_DIGIT.search(v):
        missing.append("a digit")
    if not _PASSWORD_SPECIAL.search(v):
        missing.append("a special character")
    if missing:
        if len(missing) == 1:
            detail = missing[0]
        elif len(missing) == 2:
            detail = f"{missing[0]} and {missing[1]}"
        else:
            detail = ", ".join(missing[:-1]) + f", and {missing[-1]}"
        raise ValueError(f"Password must contain {detail}.")
    return v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    full_name: str | None = None
    must_change_password: bool = False


class StaffCreate(BaseModel):
    """Admin-only: creates a User + the matching role-profile row in one
    step. `role` must be a staff role (patients are registered separately,
    by a receptionist, via POST /patients — see PatientCreate)."""

    email: EmailStr
    role: str
    full_name: str = Field(min_length=1, max_length=128)

    # doctor only
    specialization: str | None = None
    license_number: str | None = None
    # doctor / nurse / lab_technician
    department: str | None = None
    # nurse only
    shift: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_STAFF_ROLES:
            raise ValueError(f"role must be one of {VALID_STAFF_ROLES}")
        return v

    @model_validator(mode="after")
    def validate_role_specific_fields(self) -> "StaffCreate":
        if self.role == "doctor" and not (self.specialization and self.license_number and self.department):
            raise ValueError("doctor accounts require department, specialization, and license_number")
        if self.role in ("nurse", "lab_technician") and not self.department:
            raise ValueError(f"{self.role} accounts require department")
        if self.role == "nurse" and not self.shift:
            raise ValueError("nurse accounts require shift")
        return self


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: str
    full_name: str | None = None
    is_active: bool
    must_change_password: bool

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """For an already-authenticated user who knows their current password
    and wants to change it voluntarily."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class SetInitialPasswordRequest(BaseModel):
    """For a user who just verified their first-login OTP and has no
    password yet — no current_password to check, the OTP already proved
    identity."""

    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordWithOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class PreLoginRequest(BaseModel):
    email: EmailStr


class PreLoginResponse(BaseModel):
    requires_otp: bool
    requires_password: bool


class LoginWithOTPRequest(BaseModel):
    email: EmailStr
    otp: str
