from datetime import datetime

from app.models.login_log import LoginLog
from app.repositories.login_log_repository import LoginLogRepository


class LoginLogService:
    def __init__(self, login_log_repo: LoginLogRepository):
        self.login_log_repo = login_log_repo

    async def record(
        self,
        user_id: int | None,
        attempted_email: str,
        status: str,
        ip_address: str | None = None,
        device: str | None = None,
    ) -> LoginLog:
        entry = LoginLog(
            user_id=user_id,
            attempted_email=attempted_email,
            status=status,
            ip_address=ip_address,
            device=device,
        )
        self.login_log_repo.add(entry)
        await self.login_log_repo.flush()
        return entry

    async def list_recent(self, user_id: int | None = None, limit: int = 100, offset: int = 0) -> list[LoginLog]:
        return await self.login_log_repo.list_recent(user_id, limit, offset)

    async def count_recent_failures(self, user_id: int, window_start: datetime) -> int:
        return await self.login_log_repo.count_recent_failures(user_id, window_start)
