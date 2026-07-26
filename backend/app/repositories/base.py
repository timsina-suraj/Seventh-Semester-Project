"""Generic async repository — thin wrapper over AsyncSession so services
never construct SQLAlchemy queries directly (Repository Pattern)."""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, id_: int) -> ModelT | None:
        return await self.db.get(self.model, id_)

    async def get_by(self, **filters) -> ModelT | None:
        result = await self.db.execute(select(self.model).filter_by(**filters))
        return result.scalars().first()

    async def list(self, **filters) -> list[ModelT]:
        stmt = select(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.db.delete(obj)

    async def flush(self) -> None:
        await self.db.flush()

    async def commit(self) -> None:
        await self.db.commit()

    async def refresh(self, obj: ModelT) -> None:
        await self.db.refresh(obj)
