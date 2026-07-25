from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class LabResultCreate(BaseModel):
    patient_id: int
    ns1_positive: bool = False
    igg_positive: bool = False
    igm_positive: bool = False
    fever_duration_days: int = Field(ge=0, le=30, default=0)
    body_temperature_c: float = Field(ge=35.0, le=42.0)
    platelet_count: int = Field(gt=0)
    wbc_count: int = Field(gt=0)
    joint_pain: str = "None"
    headache: bool = False
    retro_orbital_pain: bool = False
    myalgia: bool = False
    rash: bool = False
    dengue_test_result: str = "Pending"

    @field_validator("joint_pain")
    @classmethod
    def validate_joint_pain(cls, v: str) -> str:
        allowed = {"None", "Moderate", "Severe"}
        if v not in allowed:
            raise ValueError(f"joint_pain must be one of {allowed}")
        return v

    @field_validator("dengue_test_result")
    @classmethod
    def validate_result(cls, v: str) -> str:
        allowed = {"Positive", "Negative", "Pending"}
        if v not in allowed:
            raise ValueError(f"dengue_test_result must be one of {allowed}")
        return v


class LabResultRead(LabResultCreate):
    id: int
    recorded_at: datetime

    class Config:
        from_attributes = True
