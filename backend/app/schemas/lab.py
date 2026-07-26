from datetime import datetime

from pydantic import BaseModel, Field


class LabTestCreate(BaseModel):
    patient_id: int
    test_name: str = Field(min_length=1, max_length=128)


class LabResultUpload(BaseModel):
    result_value: str | None = None
    result_file: str | None = None


class LabResultRead(BaseModel):
    id: int
    lab_test_id: int
    result_value: str | None
    result_file: str | None
    completed_at: datetime

    class Config:
        from_attributes = True


class LabTestRead(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    test_name: str
    status: str
    requested_at: datetime
    result: LabResultRead | None = None

    class Config:
        from_attributes = True
