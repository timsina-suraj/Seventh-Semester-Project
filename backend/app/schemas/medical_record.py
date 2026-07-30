from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

# These four columns are EncryptedString(1024)/(1024)/(2048)/(2048) -- that
# length is the ciphertext budget (base64 of nonce + AES-GCM ciphertext +
# 16-byte tag), not the plaintext one. Encrypting an N-char plaintext costs
# roughly (N + 28) * 4/3 ciphertext chars, so the max_length values below are
# picked with margin under the exact plaintext->ciphertext boundary (740/1508
# chars respectively) rather than reusing the column's own number, which
# would silently overflow the ciphertext column once encrypted.
_SHORT_CLINICAL_TEXT_MAX = 700
_LONG_CLINICAL_TEXT_MAX = 1450


class MedicalRecordCreate(BaseModel):
    patient_id: int
    doctor_id: int | None = None
    appointment_id: int | None = None
    symptoms: str | None = Field(default=None, max_length=_SHORT_CLINICAL_TEXT_MAX)
    diagnosis: str | None = Field(default=None, max_length=_SHORT_CLINICAL_TEXT_MAX)
    notes: str | None = Field(default=None, max_length=_LONG_CLINICAL_TEXT_MAX)
    treatment_plan: str | None = Field(default=None, max_length=_LONG_CLINICAL_TEXT_MAX)
    follow_up_date: date | None = None

    @field_validator("follow_up_date")
    @classmethod
    def validate_follow_up_date(cls, v: date | None) -> date | None:
        if v is not None and v < date.today():
            raise ValueError("follow_up_date cannot be in the past")
        return v


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
