from datetime import date, datetime

from pydantic import BaseModel


class MedicalRecordCreate(BaseModel):
    patient_id: int
    doctor_id: int | None = None
    appointment_id: int | None = None
    symptoms: str | None = None
    diagnosis: str | None = None
    notes: str | None = None
    treatment_plan: str | None = None
    follow_up_date: date | None = None


class MedicalRecordRead(BaseModel):
    id: int
    patient_id: int
    doctor_id: int | None
    appointment_id: int | None
    symptoms: str | None
    diagnosis: str | None
    notes: str | None
    treatment_plan: str | None
    follow_up_date: date | None
    ml_dengue_predicted: bool | None
    ml_dengue_probability: float | None
    created_at: datetime

    class Config:
        from_attributes = True
