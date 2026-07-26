from datetime import datetime, timedelta, timezone

from app.models.login_log import LoginLog
from app.models.user import User
from app.repositories.login_log_repository import LoginLogRepository


async def _make_user(db_session, email="loginlog-target@example.com") -> User:
    user = User(email=email, role="doctor")
    db_session.add(user)
    await db_session.flush()
    return user


async def _log(db_session, user_id, status, when) -> LoginLog:
    entry = LoginLog(user_id=user_id, attempted_email="x@example.com", status=status, login_time=when)
    db_session.add(entry)
    await db_session.flush()
    return entry


async def test_count_recent_failures_counts_failures_within_window(db_session):
    user = await _make_user(db_session)
    now = datetime.now(timezone.utc)
    await _log(db_session, user.id, "failed", now - timedelta(minutes=5))
    await _log(db_session, user.id, "failed", now - timedelta(minutes=3))
    repo = LoginLogRepository(db_session)

    count = await repo.count_recent_failures(user.id, now - timedelta(minutes=15))

    assert count == 2


async def test_count_recent_failures_ignores_failures_before_window(db_session):
    user = await _make_user(db_session)
    now = datetime.now(timezone.utc)
    await _log(db_session, user.id, "failed", now - timedelta(hours=2))
    repo = LoginLogRepository(db_session)

    count = await repo.count_recent_failures(user.id, now - timedelta(minutes=15))

    assert count == 0


async def test_count_recent_failures_resets_after_a_success(db_session):
    """A success in between resets the streak — failures before it must not
    count against a fresh attempt, even though they're within the window."""
    user = await _make_user(db_session)
    now = datetime.now(timezone.utc)
    await _log(db_session, user.id, "failed", now - timedelta(minutes=10))
    await _log(db_session, user.id, "failed", now - timedelta(minutes=9))
    await _log(db_session, user.id, "success", now - timedelta(minutes=8))
    await _log(db_session, user.id, "failed", now - timedelta(minutes=2))
    repo = LoginLogRepository(db_session)

    count = await repo.count_recent_failures(user.id, now - timedelta(minutes=15))

    assert count == 1


async def test_count_recent_failures_is_scoped_per_user(db_session):
    user_a = await _make_user(db_session, "user-a@example.com")
    user_b = await _make_user(db_session, "user-b@example.com")
    now = datetime.now(timezone.utc)
    await _log(db_session, user_a.id, "failed", now - timedelta(minutes=1))
    await _log(db_session, user_b.id, "failed", now - timedelta(minutes=1))
    repo = LoginLogRepository(db_session)

    count = await repo.count_recent_failures(user_a.id, now - timedelta(minutes=15))

    assert count == 1


async def test_count_recent_failures_returns_zero_with_no_logs_at_all(db_session):
    user = await _make_user(db_session)
    repo = LoginLogRepository(db_session)

    count = await repo.count_recent_failures(user.id, datetime.now(timezone.utc) - timedelta(minutes=15))

    assert count == 0
