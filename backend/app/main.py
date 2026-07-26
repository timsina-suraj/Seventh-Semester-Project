from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
