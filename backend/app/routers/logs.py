"""Admin-only views over the two Module 3 log tables. Login logs answer
'who logged in?'; audit logs answer 'what did the user do?' (spec 3)."""
from fastapi import APIRouter, Depends

from app.dependencies import get_audit_service, get_login_log_service
from app.schemas.log import AuditLogRead, LoginLogRead
from app.security.rbac import require_role
from app.services.audit_service import AuditService
from app.services.login_log_service import LoginLogService

router = APIRouter(dependencies=[Depends(require_role("admin"))])


@router.get("/audit-logs", response_model=list[AuditLogRead], tags=["audit-logs"])
async def list_audit_logs(
    user_id: int | None = None,
    entity_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    service: AuditService = Depends(get_audit_service),
):
    return await service.list_recent(user_id, entity_type, limit, offset)


@router.get("/login-logs", response_model=list[LoginLogRead], tags=["login-logs"])
async def list_login_logs(
    user_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    service: LoginLogService = Depends(get_login_log_service),
):
    return await service.list_recent(user_id, limit, offset)
