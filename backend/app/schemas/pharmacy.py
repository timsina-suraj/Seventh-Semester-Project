from datetime import datetime

from pydantic import BaseModel, Field


class PharmacyItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    unit: str = "units"
    stock_quantity: int = Field(ge=0, default=0)
    reorder_threshold: int = Field(ge=0, default=20)


class PharmacyItemUpdate(BaseModel):
    unit: str | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    reorder_threshold: int | None = Field(default=None, ge=0)


class PharmacyItemRead(BaseModel):
    id: int
    name: str
    unit: str
    stock_quantity: int
    reorder_threshold: int
    is_low_stock: bool
    updated_at: datetime

    class Config:
        from_attributes = True
