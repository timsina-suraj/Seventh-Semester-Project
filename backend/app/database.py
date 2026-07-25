"""SQLAlchemy engine/session setup.

Defaults to SQLite for zero-setup local development. Switching to MySQL is a
one-line change: set DATABASE_URL (env var or .env) to something like
    mysql+pymysql://hmms_user:password@localhost:3306/medishield_db
No application code needs to change.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
