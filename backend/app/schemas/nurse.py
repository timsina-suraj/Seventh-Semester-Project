from datetime import datetime

from pydantic import BaseModel


class PatientVitalsCreate(BaseModel):
    patient_id: int
    temperature: float | None = None
    blood_pressure: str | None = None
    heart_rate: int | None = None
    oxygen_level: float | None = None
    weight: float | None = None


class PatientVitalsRead(BaseModel):
    id: int
    patient_id: int
    nurse_id: int
    temperature: float | None
    blood_pressure: str | None
    heart_rate: int | None
    oxygen_level: float | None
    weight: float | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class MedicineAdministrationCreate(BaseModel):
    patient_id: int
    medicine: str
    dose: str | None = None


class MedicineAdministrationRead(BaseModel):
    id: int
    patient_id: int
    nurse_id: int
    medicine: str
    dose: str | None
    time_given: datetime

    class Config:
        from_attributes = True
