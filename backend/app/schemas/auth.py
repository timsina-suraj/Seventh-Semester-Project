from pydantic import BaseModel, EmailStr, Field

from app.models.user import VALID_ROLES


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    email: str
    must_change_password: bool = False


class UserCreate(BaseModel):
    email: EmailStr
    role: str

    # Only used when role == "doctor": creates the linked Doctor profile in
    # the same step so the account list and the doctor roster stay in sync.
    full_name: str | None = None
    specialization: str | None = None
    phone: str | None = None

    def validate_role(self):
        if self.role not in VALID_ROLES:
            raise ValueError(f"role must be one of {VALID_ROLES}")


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool
    must_change_password: bool

    class Config:
        from_attributes = True



class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class SelfServiceResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8, max_length=128)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordWithOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(min_length=8, max_length=128)