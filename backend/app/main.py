from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
import app.models  # noqa: F401  (registers all models with Base.metadata)
from app.routers import (
    alerts,
    appointments,
    auth,
    dashboard,
    doctors,
    lab,
    medical_records,
    ml_dengue,
    ml_diagnosis,
    patients,
    pharmacy,
    users,
    analytics,
)

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _ensure_new_columns()


def _ensure_new_columns():
    """create_all() only creates missing tables, it never alters existing
    ones. For this SQLite dev database we add any newly-introduced columns
    here so upgrades don't require a manual migration step."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    existing_columns = {col["name"] for col in inspector.get_columns("users")}
    if "must_change_password" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 0")
            )
    if "reset_otp" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN reset_otp VARCHAR(64)")
            )
    if "reset_otp_expires_at" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN reset_otp_expires_at DATETIME")
            )
    if "login_otp" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN login_otp VARCHAR(64)")
            )
    if "login_otp_expires_at" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN login_otp_expires_at DATETIME")
            )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(patients.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(lab.router)
app.include_router(pharmacy.router)
app.include_router(medical_records.router)
app.include_router(dashboard.router)
app.include_router(ml_dengue.router)
app.include_router(ml_diagnosis.router)
app.include_router(alerts.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}


@app.get("/health")
def health():
    return {"status": "healthy"}