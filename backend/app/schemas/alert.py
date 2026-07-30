from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.alert import VALID_ALERT_STATUSES


class AlertRead(BaseModel):
    id: int
    alert_type: str
    district: str | None
    risk_level: str | None
    message: str
    status: str
    date: datetime

    class Config:
        from_attributes = True


class AlertUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_ALERT_STATUSES:
            raise ValueError(f"status must be one of {VALID_ALERT_STATUSES}")
        return v
