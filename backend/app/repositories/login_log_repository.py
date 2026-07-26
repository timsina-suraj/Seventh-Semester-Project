from datetime import datetime, timezone

from sqlalchemy import func, select

from app.models.login_log import LoginLog
from app.repositories.base import BaseRepository


def _as_aware(dt: datetime | None) -> datetime | None:
    """SQLite drops tzinfo on round-trip, so a timestamp fetched back from
    the DB comes back naive — normalize before comparing/max()-ing it
    against a freshly-computed aware datetime, or Python raises."""
    if dt is None or dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


class LoginLogRepository(BaseRepository[LoginLog]):
    model = LoginLog

    async def list_recent(
        self, user_id: int | None = None, limit: int = 100, offset: int = 0
    ) -> list[LoginLog]:
        stmt = select(LoginLog).order_by(LoginLog.login_time.desc())
        if user_id is not None:
            stmt = stmt.where(LoginLog.user_id == user_id)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_recent_failures(self, user_id: int, window_start: datetime) -> int:
        """Consecutive failed attempts since the more recent of `window_start`
        or the user's last successful login — a success always resets the
        counter, matching standard account-lockout semantics (otherwise a
        failure from before an unrelated successful login would still count
        against a fresh attempt)."""
        last_success = _as_aware(
            await self.db.scalar(
                select(func.max(LoginLog.login_time)).where(
                    LoginLog.user_id == user_id, LoginLog.status == "success"
                )
            )
        )
        since = max(window_start, last_success) if last_success else window_start

        count = await self.db.scalar(
            select(func.count()).select_from(LoginLog).where(
                LoginLog.user_id == user_id,
                LoginLog.status == "failed",
                LoginLog.login_time >= since,
            )
        )
        return count or 0
