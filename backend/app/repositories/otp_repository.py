from datetime import datetime, timezone

from sqlalchemy import delete, or_, select

from app.models.otp_request import OtpRequest
from app.repositories.base import BaseRepository


class OtpRequestRepository(BaseRepository[OtpRequest]):
    model = OtpRequest

    async def get_latest_active(self, user_id: int, purpose: str) -> OtpRequest | None:
        """The newest not-yet-used row for (user_id, purpose), regardless of
        whether it has expired — callers check expiry themselves so they can
        raise a specific OtpExpiredError vs OtpInvalidError."""
        stmt = (
            select(OtpRequest)
            .where(
                OtpRequest.user_id == user_id,
                OtpRequest.purpose == purpose,
                OtpRequest.used_at.is_(None),
            )
            .order_by(OtpRequest.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def mark_used(self, otp: OtpRequest) -> None:
        otp.used_at = datetime.now(timezone.utc)
        await self.flush()

    async def increment_attempts(self, otp: OtpRequest) -> None:
        otp.attempt_count += 1
        await self.flush()

    async def delete_stale(self, cutoff: datetime) -> int:
        """Purges rows that no longer serve any purpose: already-verified
        OTPs (used_at set — inert forever the moment they're used, since
        get_latest_active() can never select them again, so there's no
        reason to wait before removing them) and expired-but-never-used OTPs
        older than `cutoff` (callers typically pass now() minus a retention
        window, e.g. 24-48h, so a just-expired row stays visible for a
        little while during troubleshooting). Does not commit — the caller
        controls the transaction. Returns the number of rows deleted."""
        stmt = delete(OtpRequest).where(
            or_(OtpRequest.used_at.is_not(None), OtpRequest.expires_at < cutoff)
        )
        result = await self.db.execute(stmt)
        return result.rowcount
