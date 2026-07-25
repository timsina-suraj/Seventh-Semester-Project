from datetime import datetime

from pydantic import BaseModel


class MedicalRecordCreate(BaseModel):
    patient_id: int
    doctor_id: int | None = None
    symptoms: str | None = None
    diagnosis: str | None = None
    lab_result: str | None = None
    prescription: str | None = None
    prescribed_tests: str | None = None
    medical_history: str | None = None
    clinical_history: str | None = None
    doctor_note: str | None = None


class MedicalRecordRead(BaseModel):
    id: int
    patient_id: int
    doctor_id: int | None
    symptoms: str | None
    diagnosis: str | None
    lab_result: str | None
    prescription: str | None
    prescribed_tests: str | None
    medical_history: str | None
    clinical_history: str | None
    doctor_note: str | None
    ml_dengue_predicted: bool | None
    ml_dengue_probability: float | None
    date: datetime

    class Config:
        from_attributes = True
