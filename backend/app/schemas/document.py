from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: int
    patient_id: int
    uploaded_by_user_id: int
    category: str
    original_filename: str
    content_type: str
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True
