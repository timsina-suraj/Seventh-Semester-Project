from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
import app.models  # noqa: F401  (registers all models with Base.metadata, used by Alembic)
from app.routers import (
    alerts,
    analytics,
    appointments,
    auth,
    dashboard,
    doctors,
    documents,
    lab,
    logs,
    medical_records,
    ml_dengue,
    ml_diagnosis,
    nurse,
    patient_history,
    patients,
    pharmacy,
    prescriptions,
    staff,
    users,
)

configure_logging()

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    # Enabling SQLite's foreign_keys pragma (see database.py) means deleting
    # a row that's still referenced elsewhere -- e.g. a patient who has lab
    # tests, prescriptions, or vitals recorded, none of which cascade at the
    # ORM level -- now raises this instead of silently leaving an orphaned
    # row. Without this handler that would surface as a raw 500 with a
    # SQLite stack trace; this turns it into a clean, actionable 409 instead.
    return JSONResponse(
        status_code=409,
        content={
            "detail": (
                "This action conflicts with related records that still exist "
                "(e.g. appointments, lab tests, prescriptions, or other linked "
                "data) and cannot be completed until those are removed first."
            )
        },
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
app.include_router(logs.router)
app.include_router(prescriptions.router)
app.include_router(patient_history.router)
app.include_router(nurse.router)
app.include_router(documents.router)
app.include_router(staff.router)


@app.get("/")
def root():
    return {"status": "ok", "app": settings.app_name}


@app.get("/health")
def health():
    return {"status": "healthy"}
