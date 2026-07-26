from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.medicine import Medicine
from app.repositories.base import BaseRepository


class MedicineRepository(BaseRepository[Medicine]):
    model = Medicine

    async def get_with_inventory(self, id_: int) -> Medicine | None:
        result = await self.db.execute(
            select(Medicine).options(selectinload(Medicine.inventory)).where(Medicine.id == id_)
        )
        return result.scalars().first()

    async def list_with_inventory(self, search: str | None = None) -> list[Medicine]:
        stmt = select(Medicine).options(selectinload(Medicine.inventory))
        if search:
            stmt = stmt.where(Medicine.name.ilike(f"%{search}%"))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
