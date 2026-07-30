import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# "120/80" style, 2-3 digit systolic/diastolic — loose enough to accept real
# extremes, tight enough to reject stray text in a field a chart depends on.
_BLOOD_PRESSURE_RE = re.compile(r"^\d{2,3}/\d{2,3}$")


class PatientVitalsCreate(BaseModel):
    patient_id: int
    # Bounds are plausibility guards against typos/garbage, not clinical
    # thresholds — e.g. 300 bpm and 45C are not "normal" but are within what
    # a real (if critical) patient reading could show.
    temperature: float | None = Field(default=None, ge=25.0, le=45.0)
    blood_pressure: str | None = None
    heart_rate: int | None = Field(default=None, ge=0, le=300)
    oxygen_level: float | None = Field(default=None, ge=0, le=100)
    weight: float | None = Field(default=None, gt=0, le=500)

    @field_validator("blood_pressure")
    @classmethod
    def validate_blood_pressure(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return v
        if not _BLOOD_PRESSURE_RE.match(v):
            raise ValueError('blood_pressure must look like "120/80"')
        systolic, diastolic = (int(part) for part in v.split("/"))
        if not (40 <= systolic <= 300) or not (20 <= diastolic <= 200):
            raise ValueError("blood_pressure readings are out of plausible range")
        return v


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
    medicine: str = Field(min_length=1, max_length=128)
    dose: str | None = Field(default=None, max_length=64)


class MedicineAdministrationRead(BaseModel):
    id: int
    patient_id: int
    nurse_id: int
    medicine: str
    dose: str | None
    time_given: datetime

    class Config:
        from_attributes = True
