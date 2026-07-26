from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, audit_repo: AuditLogRepository):
        self.audit_repo = audit_repo

    async def record(
        self,
        user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
        )
        self.audit_repo.add(entry)
        await self.audit_repo.flush()
        return entry

    async def list_recent(
        self, user_id: int | None = None, entity_type: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[AuditLog]:
        return await self.audit_repo.list_recent(user_id, entity_type, limit, offset)
