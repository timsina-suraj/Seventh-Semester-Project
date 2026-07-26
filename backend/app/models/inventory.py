from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id"), unique=True, nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, default=0)
    # Not in spec's literal table — powers the existing low-stock dashboard
    # stat and Pharmacy page badge; dropping it would regress a working
    # feature the spec doesn't forbid extending for.
    reorder_threshold: Mapped[int] = mapped_column(Integer, default=20)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    medicine = relationship("Medicine", back_populates="inventory")

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.reorder_threshold
