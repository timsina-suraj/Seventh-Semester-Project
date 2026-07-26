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
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_async_engine(settings.database_url, connect_args=connect_args)
SessionLocal = async_sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as db:
        yield db
