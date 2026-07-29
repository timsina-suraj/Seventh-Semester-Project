from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class PrescriptionItemCreate(BaseModel):
    medicine_name: str = Field(min_length=1, max_length=128)
    medicine_id: int | None = None
    quantity: int | None = Field(default=None, ge=1)
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None
    instructions: str | None = None

    @model_validator(mode="after")
    def validate_quantity_paired_with_medicine_id(self) -> "PrescriptionItemCreate":
        if self.medicine_id is not None and self.quantity is None:
            raise ValueError("quantity is required when medicine_id is set")
        if self.medicine_id is None and self.quantity is not None:
            raise ValueError("quantity can only be set together with medicine_id")
        return self


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
