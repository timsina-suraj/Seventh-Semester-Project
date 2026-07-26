from datetime import datetime, timedelta, timezone

import pytest

from app.core.exceptions import (
    OtpAttemptsExceededError,
    OtpExpiredError,
    OtpInvalidError,
    OtpNotRequestedError,
    RateLimitedError,
)
from app.models.otp_request import OtpRequest
from app.models.user import User
from app.repositories.otp_repository import OtpRequestRepository
from app.security.auth import hash_password
from app.services.otp_service import OtpService


async def _make_user(db_session) -> User:
    user = User(email="otp-target@example.com", role="doctor")
    db_session.add(user)
    await db_session.flush()
    return user


async def test_request_otp_returns_six_digit_code(db_session):
    user = await _make_user(db_session)
    service = OtpService(OtpRequestRepository(db_session))

    code = await service.request_otp(user.id, "first_login")

    assert len(code) == 6
    assert code.isdigit()


async def test_verify_otp_succeeds_with_correct_code(db_session):
    user = await _make_user(db_session)
    service = OtpService(OtpRequestRepository(db_session))
    code = await service.request_otp(user.id, "first_login")

    await service.verify_otp(user.id, "first_login", code)  # should not raise


async def test_verify_otp_rejects_wrong_code_and_counts_attempt(db_session):
    user = await _make_user(db_session)
    repo = OtpRequestRepository(db_session)
    service = OtpService(repo)
    await service.request_otp(user.id, "first_login")

    with pytest.raises(OtpInvalidError):
        await service.verify_otp(user.id, "first_login", "000000")

    otp = await repo.get_latest_active(user.id, "first_login")
    assert otp.attempt_count == 1


async def test_verify_otp_without_a_request_raises(db_session):
    user = await _make_user(db_session)
    service = OtpService(OtpRequestRepository(db_session))

    with pytest.raises(OtpNotRequestedError):
        await service.verify_otp(user.id, "first_login", "123456")


async def test_verify_otp_expired_raises(db_session):
    user = await _make_user(db_session)
    repo = OtpRequestRepository(db_session)
    service = OtpService(repo)
    code = await service.request_otp(user.id, "first_login")

    otp = await repo.get_latest_active(user.id, "first_login")
    otp.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.flush()

    with pytest.raises(OtpExpiredError):
        await service.verify_otp(user.id, "first_login", code)


async def test_verify_otp_attempts_exceeded(db_session, monkeypatch):
    monkeypatch.setattr("app.services.otp_service.settings.otp_max_attempts", 2)
    user = await _make_user(db_session)
    service = OtpService(OtpRequestRepository(db_session))
    await service.request_otp(user.id, "first_login")

    for _ in range(2):
        with pytest.raises(OtpInvalidError):
            await service.verify_otp(user.id, "first_login", "000000")

    with pytest.raises(OtpAttemptsExceededError):
        await service.verify_otp(user.id, "first_login", "000000")


async def test_request_otp_rate_limited_within_cooldown(db_session):
    user = await _make_user(db_session)
    service = OtpService(OtpRequestRepository(db_session))
    await service.request_otp(user.id, "first_login")

    with pytest.raises(RateLimitedError):
        await service.request_otp(user.id, "first_login")


async def test_purposes_are_independent(db_session):
    """A first_login OTP must not verify against a password_reset request
    and vice versa — otherwise an attacker who triggers a reset email could
    hijack a still-open first-login session, or vice versa."""
    user = await _make_user(db_session)
    service = OtpService(OtpRequestRepository(db_session))
    login_code = await service.request_otp(user.id, "first_login")
    await service.request_otp(user.id, "password_reset")

    with pytest.raises(OtpInvalidError):
        await service.verify_otp(user.id, "password_reset", login_code)


async def test_delete_stale_removes_used_rows_regardless_of_age(db_session):
    user = await _make_user(db_session)
    repo = OtpRequestRepository(db_session)
    used = OtpRequest(
        user_id=user.id, otp_hash=hash_password("111111"), purpose="first_login",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        used_at=datetime.now(timezone.utc),  # used seconds ago — still stale per delete_stale
    )
    db_session.add(used)
    await db_session.flush()

    deleted = await repo.delete_stale(datetime.now(timezone.utc) - timedelta(days=365))
    await db_session.commit()

    assert deleted == 1
    assert await repo.get(used.id) is None


async def test_delete_stale_removes_expired_unused_rows_before_cutoff(db_session):
    user = await _make_user(db_session)
    repo = OtpRequestRepository(db_session)
    old_expired = OtpRequest(
        user_id=user.id, otp_hash=hash_password("111111"), purpose="first_login",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=72),
    )
    db_session.add(old_expired)
    await db_session.flush()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    deleted = await repo.delete_stale(cutoff)
    await db_session.commit()

    assert deleted == 1
    assert await repo.get(old_expired.id) is None


async def test_delete_stale_keeps_unused_rows_not_yet_past_cutoff(db_session):
    user = await _make_user(db_session)
    repo = OtpRequestRepository(db_session)
    still_active = OtpRequest(
        user_id=user.id, otp_hash=hash_password("111111"), purpose="first_login",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    recently_expired = OtpRequest(
        user_id=user.id, otp_hash=hash_password("222222"), purpose="password_reset",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),  # expired, but within the retention window
    )
    db_session.add_all([still_active, recently_expired])
    await db_session.flush()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
    deleted = await repo.delete_stale(cutoff)
    await db_session.commit()

    assert deleted == 0
    assert await repo.get(still_active.id) is not None
    assert await repo.get(recently_expired.id) is not None
