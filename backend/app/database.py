"""SQLAlchemy async engine/session setup.

Defaults to SQLite (via aiosqlite) for zero-setup local development.
Switching to MySQL is a one-line change: set DATABASE_URL (env var or .env)
to something like
    mysql+aiomysql://hmms_user:password@localhost:3306/medishield_db
No application code needs to change.

Alembic migrations run against `settings.sync_database_url` instead (a
plain sync driver) — see alembic/env.py. This is the standard pattern for
async SQLAlchemy apps: the app talks to the DB asynchronously at runtime,
migrations run synchronously and out-of-band.
"""
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_async_engine(settings.database_url, connect_args=connect_args)

if _is_sqlite:
    # SQLite does not enforce FOREIGN KEY constraints unless this pragma is
    # set on every connection -- it is off by default and is NOT a
    # database-file-level setting, so it has to be applied here rather than
    # once via a migration. MySQL (the other DATABASE_URL this app supports,
    # see the module docstring) enforces foreign keys by default and needs
    # no equivalent. Without this, an appointment/lab test/prescription/etc.
    # could silently reference a patient_id that doesn't exist on SQLite.
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = async_sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as db:
        yield db
