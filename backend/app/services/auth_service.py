"""Login / OTP-login / change-password / forgot-reset-password — Module 3.

Change Password (authenticated, re-enter current password) and Reset
Password (unauthenticated, OTP-driven) are kept as two distinct methods per
spec, sharing OtpService only for the reset path's OTP purpose
('password_reset'). The first-login OTP path ('first_login') activates the
account and issues a token, then `set_initial_password` finishes onboarding
without requiring a "current password" that was never revealed to the user
(there isn't one — see registration_service, password_hash starts NULL)."""
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks
from sqlalchemy import select

from app.config import settings
from app.core.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    OtpError,
    RateLimitedError,
    ValidationError,
)
from app.core.logging import get_logger
from app.models.admin import Admin
from app.models.doctor import Doctor
from app.models.lab_technician import LabTechnician
from app.models.nurse import Nurse
from app.models.patient import Patient
from app.models.receptionist import Receptionist
from app.models.user import User
from app.repositories.user_repository import UserRepository

# Role-specific profile tables hold the display name; `users` itself only
# has login/security fields. Admin's column is named `name`, everyone
# else's is `full_name` — normalized here so callers don't care.
_PROFILE_MODEL_BY_ROLE = {
    "doctor": Doctor,
    "nurse": Nurse,
    "receptionist": Receptionist,
    "lab_technician": LabTechnician,
    "patient": Patient,
}
from app.schemas.auth import PreLoginResponse
from app.security.auth import hash_password, verify_password
from app.services.audit_service import AuditService
from app.services.email_service import send_otp_email, send_password_reset_otp_email
from app.services.login_log_service import LoginLogService
from app.services.otp_service import OtpService

logger = get_logger(__name__)


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        otp_service: OtpService,
        login_log_service: LoginLogService,
        audit_service: AuditService,
    ):
        self.user_repo = user_repo
        self.otp_service = otp_service
        self.login_log_service = login_log_service
        self.audit_service = audit_service

    async def get_full_name(self, user: User) -> str | None:
        """Looks up the display name from the user's role-specific profile
        table, for the login response's greeting (see Token.full_name)."""
        db = self.user_repo.db
        if user.role == "admin":
            result = await db.execute(select(Admin.name).filter_by(user_id=user.id))
        else:
            model = _PROFILE_MODEL_BY_ROLE.get(user.role)
            if model is None:
                return None
            result = await db.execute(select(model.full_name).filter_by(user_id=user.id))
        return result.scalar_one_or_none()

    async def _enforce_not_locked(
        self, user: User, email: str, ip_address: str | None, device: str | None
    ) -> None:
        """Rejects the attempt outright once too many recent failures have
        piled up for this account — checked before the credential itself is
        even verified, so a correct guess during lockout still doesn't get
        in (standard brute-force defense; the counter only clears once
        enough failures age out of the window, or on a fresh success)."""
        window_start = datetime.now(timezone.utc) - timedelta(minutes=settings.login_lockout_window_minutes)
        recent_failures = await self.login_log_service.count_recent_failures(user.id, window_start)
        if recent_failures >= settings.login_max_failed_attempts:
            await self.login_log_service.record(user.id, email, "failed", ip_address, device)
            await self.user_repo.commit()
            logger.warning("account_locked_out user_id=%s recent_failures=%s", user.id, recent_failures)
            raise RateLimitedError(
                f"Too many failed login attempts. Please wait up to "
                f"{settings.login_lockout_window_minutes} minute(s) and try again."
            )

    async def login(
        self, email: str, password: str, ip_address: str | None = None, device: str | None = None
    ) -> User:
        user = await self.user_repo.get_by_email(email)
        if user is not None:
            await self._enforce_not_locked(user, email, ip_address, device)

        if not user or not verify_password(password, user.password_hash):
            await self.login_log_service.record(user.id if user else None, email, "failed", ip_address, device)
            await self.user_repo.commit()
            raise InvalidCredentialsError()
        if not user.is_active:
            await self.login_log_service.record(user.id, email, "failed", ip_address, device)
            await self.user_repo.commit()
            raise AccountDisabledError()

        await self.login_log_service.record(user.id, email, "success", ip_address, device)
        await self.user_repo.commit()
        return user

    async def pre_login(self, email: str, background_tasks: BackgroundTasks | None = None) -> PreLoginResponse:
        user = await self.user_repo.get_by_email(email)
        if not user:
            # Don't reveal whether the account exists.
            return PreLoginResponse(requires_otp=False, requires_password=True)

        if not user.must_change_password:
            return PreLoginResponse(requires_otp=False, requires_password=True)

        try:
            otp = await self.otp_service.request_otp(user.id, "first_login")
            await self.user_repo.commit()
            if background_tasks is not None:
                background_tasks.add_task(send_otp_email, user.email, otp)
            else:
                send_otp_email(user.email, otp)
        except OtpError:
            pass  # a still-valid OTP was already sent recently; nothing more to do

        return PreLoginResponse(requires_otp=True, requires_password=False)

    async def login_with_otp(
        self, email: str, otp: str, ip_address: str | None = None, device: str | None = None
    ) -> User:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError("Incorrect email or OTP")
        await self._enforce_not_locked(user, email, ip_address, device)
        if not user.must_change_password:
            raise ValidationError("User has already set a password. Use standard login.")

        try:
            await self.otp_service.verify_otp(user.id, "first_login", otp)
        except OtpError:
            await self.login_log_service.record(user.id, email, "failed", ip_address, device)
            await self.user_repo.commit()
            raise

        user.is_active = True
        await self.login_log_service.record(user.id, email, "success", ip_address, device)
        await self.user_repo.commit()
        await self.user_repo.refresh(user)
        return user

    async def set_initial_password(self, user: User, new_password: str) -> User:
        if not user.must_change_password:
            raise ValidationError("Password already set — use change-password instead")
        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        await self.audit_service.record(user.id, "set_initial_password", "user", user.id)
        await self.user_repo.commit()
        await self.user_repo.refresh(user)
        logger.info("initial_password_set user_id=%s", user.id)
        return user

    async def change_password(self, user: User, current_password: str, new_password: str) -> User:
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError("Current password is incorrect")
        if new_password == current_password:
            raise ValidationError("New password must be different from the current one")

        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        await self.audit_service.record(user.id, "changed_password", "user", user.id)
        await self.user_repo.commit()
        await self.user_repo.refresh(user)
        return user

    async def forgot_password(self, email: str, background_tasks: BackgroundTasks | None = None) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return  # don't reveal whether the account exists

        try:
            otp = await self.otp_service.request_otp(user.id, "password_reset")
        except OtpError:
            return  # a still-valid reset OTP was already sent recently

        await self.user_repo.commit()
        if background_tasks is not None:
            background_tasks.add_task(send_password_reset_otp_email, user.email, otp)
        else:
            send_password_reset_otp_email(user.email, otp)

    async def admin_force_password_reset(self, target_user: User, actor_user_id: int) -> None:
        """Admin-initiated reset: clears the password and puts the account
        back through the first-login OTP flow (same as a brand-new staff
        account — reuses that infrastructure entirely rather than adding a
        second reset mechanism). No new email template: the OTP email fires
        automatically on the user's next /auth/pre-login, exactly like a
        first-time login."""
        target_user.password_hash = None
        target_user.must_change_password = True
        await self.audit_service.record(actor_user_id, "admin_forced_password_reset", "user", target_user.id)
        await self.user_repo.commit()
        logger.info("admin_forced_password_reset user_id=%s by actor_id=%s", target_user.id, actor_user_id)

    async def reset_password(self, email: str, otp: str, new_password: str) -> None:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValidationError("Invalid request")

        await self.otp_service.verify_otp(user.id, "password_reset", otp)

        user.password_hash = hash_password(new_password)
        user.must_change_password = False
        user.is_active = True
        await self.audit_service.record(user.id, "reset_password", "user", user.id)
        await self.user_repo.commit()
