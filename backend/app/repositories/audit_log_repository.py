from sqlalchemy import select

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def list_recent(
        self,
        user_id: int | None = None,
        entity_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())
        if user_id is not None:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if entity_type is not None:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
