from datetime import date

from pydantic import BaseModel, Field, field_validator


class MedicineCreate(BaseModel):
    """Creates a Medicine + its initial Inventory row in one step (see
    PharmacyService.create_medicine_with_stock) — keeps the pre-split
    single-form UX even though the schema is now two tables."""

    name: str = Field(min_length=1, max_length=128)
    category: str | None = None
    expiry_date: date | None = None
    unit: str = "units"
    stock_quantity: int = Field(ge=0, default=0)
    reorder_threshold: int = Field(ge=0, default=20)

    @field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, v: date | None) -> date | None:
        # Entering a medicine that's already expired as new stock is either
        # a typo'd year or dead stock that shouldn't be added at all --
        # either way it's not something a create-new-stock form should accept.
        if v is not None and v <= date.today():
            raise ValueError("expiry_date must be in the future")
        return v


class MedicineStockUpdate(BaseModel):
    stock_quantity: int | None = Field(default=None, ge=0)
    reorder_threshold: int | None = Field(default=None, ge=0)


class MedicineRead(BaseModel):
    """Flat read shape — joins Medicine + Inventory so the frontend keeps
    working against the same fields it used before the split."""

    id: int
    name: str
    category: str | None
    expiry_date: date | None
    unit: str
    stock_quantity: int
    reorder_threshold: int
    is_low_stock: bool

    @classmethod
    def from_medicine(cls, medicine) -> "MedicineRead":
        inv = medicine.inventory
        return cls(
            id=medicine.id,
            name=medicine.name,
            category=medicine.category,
            expiry_date=medicine.expiry_date,
            unit=medicine.unit,
            stock_quantity=inv.quantity if inv else 0,
            reorder_threshold=inv.reorder_threshold if inv else 0,
            is_low_stock=inv.is_low_stock if inv else True,
        )
