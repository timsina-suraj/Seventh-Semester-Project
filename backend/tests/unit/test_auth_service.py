import pytest

from app.core.exceptions import (
    AccountDisabledError,
    InvalidCredentialsError,
    RateLimitedError,
    ValidationError,
)
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.login_log_repository import LoginLogRepository
from app.repositories.otp_repository import OtpRequestRepository
from app.repositories.user_repository import UserRepository
from app.security.auth import hash_password
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.login_log_service import LoginLogService
from app.services.otp_service import OtpService


def _build_service(db_session) -> AuthService:
    return AuthService(
        UserRepository(db_session),
        OtpService(OtpRequestRepository(db_session)),
        LoginLogService(LoginLogRepository(db_session)),
        AuditService(AuditLogRepository(db_session)),
    )


async def _active_user(db_session, password="Correct@123") -> User:
    user = User(
        email="staff@example.com",
        role="doctor",
        password_hash=hash_password(password),
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def test_login_succeeds_with_correct_password(db_session):
    user = await _active_user(db_session)
    service = _build_service(db_session)

    result = await service.login(user.email, "Correct@123")

    assert result.id == user.id


async def test_login_rejects_wrong_password(db_session):
    await _active_user(db_session)
    service = _build_service(db_session)

    with pytest.raises(InvalidCredentialsError):
        await service.login("staff@example.com", "WrongPassword")


async def test_login_rejects_unknown_email(db_session):
    service = _build_service(db_session)

    with pytest.raises(InvalidCredentialsError):
        await service.login("nobody@example.com", "whatever")


async def test_login_rejects_disabled_account(db_session):
    user = User(
        email="disabled@example.com",
        role="doctor",
        password_hash=hash_password("Correct@123"),
        is_active=False,
        must_change_password=False,
    )
    db_session.add(user)
    await db_session.flush()
    service = _build_service(db_session)

    with pytest.raises(AccountDisabledError):
        await service.login(user.email, "Correct@123")


async def test_login_rejects_account_with_no_password_yet(db_session):
    """A freshly-registered account (password_hash=None) must not be
    reachable via the normal login path — it has to go through pre-login
    -> OTP instead."""
    user = User(email="fresh@example.com", role="nurse")  # defaults: no password, inactive
    db_session.add(user)
    await db_session.flush()
    service = _build_service(db_session)

    with pytest.raises(InvalidCredentialsError):
        await service.login(user.email, "anything")


async def test_login_locks_out_after_max_failed_attempts(db_session, monkeypatch):
    monkeypatch.setattr("app.services.auth_service.settings.login_max_failed_attempts", 3)
    monkeypatch.setattr("app.services.auth_service.settings.login_lockout_window_minutes", 15)
    user = await _active_user(db_session)
    service = _build_service(db_session)

    for _ in range(3):
        with pytest.raises(InvalidCredentialsError):
            await service.login(user.email, "WrongPassword")

    # Even the *correct* password is rejected now — lockout is checked
    # before the credential itself, so a right guess during lockout still
    # doesn't get in.
    with pytest.raises(RateLimitedError):
        await service.login(user.email, "Correct@123")


async def test_login_below_threshold_still_allows_correct_password(db_session, monkeypatch):
    monkeypatch.setattr("app.services.auth_service.settings.login_max_failed_attempts", 3)
    user = await _active_user(db_session)
    service = _build_service(db_session)

    for _ in range(2):
        with pytest.raises(InvalidCredentialsError):
            await service.login(user.email, "WrongPassword")

    result = await service.login(user.email, "Correct@123")

    assert result.id == user.id


async def test_login_lockout_is_scoped_per_account(db_session, monkeypatch):
    monkeypatch.setattr("app.services.auth_service.settings.login_max_failed_attempts", 2)
    locked_user = await _active_user(db_session)
    other_user = User(
        email="other-account@example.com", role="nurse", password_hash=hash_password("Other@123"),
        is_active=True, must_change_password=False,
    )
    db_session.add(other_user)
    await db_session.flush()
    service = _build_service(db_session)

    for _ in range(2):
        with pytest.raises(InvalidCredentialsError):
            await service.login(locked_user.email, "WrongPassword")
    with pytest.raises(RateLimitedError):
        await service.login(locked_user.email, "Correct@123")

    # A different account's own attempts are unaffected by the first one's lockout.
    result = await service.login(other_user.email, "Other@123")
    assert result.id == other_user.id


async def test_login_with_otp_also_respects_lockout(db_session, monkeypatch):
    monkeypatch.setattr("app.services.auth_service.settings.login_max_failed_attempts", 2)
    user = User(
        email="pending-first-login@example.com", role="nurse",
        is_active=False, must_change_password=True,
    )
    db_session.add(user)
    await db_session.flush()
    service = _build_service(db_session)

    for _ in range(2):
        with pytest.raises(InvalidCredentialsError):
            await service.login(user.email, "WrongPassword")

    with pytest.raises(RateLimitedError):
        await service.login_with_otp(user.email, "000000")


async def test_change_password_requires_correct_current_password(db_session):
    user = await _active_user(db_session)
    service = _build_service(db_session)

    with pytest.raises(InvalidCredentialsError):
        await service.change_password(user, "WrongCurrent", "NewPass@123")


async def test_change_password_rejects_same_password(db_session):
    user = await _active_user(db_session)
    service = _build_service(db_session)

    with pytest.raises(ValidationError):
        await service.change_password(user, "Correct@123", "Correct@123")


async def test_change_password_success_clears_must_change_flag(db_session):
    user = User(
        email="mustchange@example.com",
        role="doctor",
        password_hash=hash_password("Temp@1234"),
        is_active=True,
        must_change_password=True,
    )
    db_session.add(user)
    await db_session.flush()
    service = _build_service(db_session)

    updated = await service.change_password(user, "Temp@1234", "Brand@New1")

    assert updated.must_change_password is False


async def test_set_initial_password_rejects_when_already_set(db_session):
    user = await _active_user(db_session)  # must_change_password=False already
    service = _build_service(db_session)

    with pytest.raises(ValidationError):
        await service.set_initial_password(user, "SomePass@1")
