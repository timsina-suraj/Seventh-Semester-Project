from datetime import datetime

from pydantic import BaseModel, Field


class PrescriptionItemCreate(BaseModel):
    medicine_name: str = Field(min_length=1, max_length=128)
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    instructions: str | None = None


class PrescriptionItemRead(PrescriptionItemCreate):
    id: int

    class Config:
        from_attributes = True


class PrescriptionCreate(BaseModel):
    patient_id: int
    medical_record_id: int | None = None
    items: list[PrescriptionItemCreate] = Field(min_length=1)


class PrescriptionRead(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    medical_record_id: int | None
    created_at: datetime
    items: list[PrescriptionItemRead]

    class Config:
        from_attributes = True
