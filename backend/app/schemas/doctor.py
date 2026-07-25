from pydantic import BaseModel, Field


class DoctorCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=128)
    specialization: str = "General Physician"
    phone: str | None = None
    is_available: bool = True


class DoctorUpdate(BaseModel):
    full_name: str | None = None
    specialization: str | None = None
    phone: str | None = None
    is_available: bool | None = None


class DoctorRead(BaseModel):
    id: int
    full_name: str
    specialization: str
    phone: str | None
    is_available: bool

    class Config:
        from_attributes = True
