from datetime import datetime

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    timestamp: datetime
    ip_address: str | None

    class Config:
        from_attributes = True


class LoginLogRead(BaseModel):
    id: int
    user_id: int | None
    attempted_email: str
    ip_address: str | None
    device: str | None
    login_time: datetime
    status: str

    class Config:
        from_attributes = True
