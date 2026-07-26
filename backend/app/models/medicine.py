from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Not in spec's literal table, but needed to render the existing
    # Pharmacy UI ("tablets", "bottles", ...) without regressing it.
    unit: Mapped[str] = mapped_column(String(32), default="units")

    inventory = relationship("Inventory", back_populates="medicine", uselist=False, cascade="all, delete-orphan")
