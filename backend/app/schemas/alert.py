from datetime import datetime

from pydantic import BaseModel


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
