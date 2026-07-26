"""Purpose-scoped OTP issue/verify with expiry, attempt-limit, and a resend
cooldown (Module 3: 'OTP expiry, OTP attempt limit, OTP rate limiting')."""
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.core.exceptions import (
    OtpAttemptsExceededError,
    OtpExpiredError,
    OtpInvalidError,
    OtpNotRequestedError,
    RateLimitedError,
)
from app.core.logging import get_logger
from app.models.otp_request import OtpRequest
from app.repositories.otp_repository import OtpRequestRepository
from app.security.auth import generate_otp, hash_password, verify_password

logger = get_logger(__name__)


def _as_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


class OtpService:
    def __init__(self, otp_repo: OtpRequestRepository):
        self.otp_repo = otp_repo

    async def request_otp(self, user_id: int, purpose: str) -> str:
        """Creates a new OTP row and returns the raw (unhashed) code for the
        caller to email. Raises RateLimitedError if the previous OTP for
        this (user, purpose) is still within its resend cooldown."""
        existing = await self.otp_repo.get_latest_active(user_id, purpose)
        if existing is not None:
            elapsed = (datetime.now(timezone.utc) - _as_aware(existing.created_at)).total_seconds()
            if elapsed < settings.otp_resend_cooldown_seconds:
                raise RateLimitedError(
                    f"Please wait {int(settings.otp_resend_cooldown_seconds - elapsed)}s before requesting another OTP"
                )
            # Superseded — mark used so it can no longer be verified.
            await self.otp_repo.mark_used(existing)

        code = generate_otp()
        otp = OtpRequest(
            user_id=user_id,
            otp_hash=hash_password(code),
            purpose=purpose,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes),
        )
        self.otp_repo.add(otp)
        await self.otp_repo.flush()
        logger.info("otp_issued user_id=%s purpose=%s", user_id, purpose)
        return code

    async def verify_otp(self, user_id: int, purpose: str, code: str) -> None:
        otp = await self.otp_repo.get_latest_active(user_id, purpose)
        if otp is None:
            raise OtpNotRequestedError()
        if otp.attempt_count >= settings.otp_max_attempts:
            raise OtpAttemptsExceededError()
        if datetime.now(timezone.utc) > _as_aware(otp.expires_at):
            raise OtpExpiredError()
        if not verify_password(code, otp.otp_hash):
            await self.otp_repo.increment_attempts(otp)
            raise OtpInvalidError()

        await self.otp_repo.mark_used(otp)
        logger.info("otp_verified user_id=%s purpose=%s", user_id, purpose)
