from datetime import date, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.database import get_db
from app.dependencies import (
    get_appointment_repository,
    get_doctor_repository,
    get_medical_record_repository,
    get_patient_repository,
)
from app.models.doctor import Doctor
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.staff_repository import DoctorRepository
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordRead
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.patient_access import doctor_patient_ids
from app.services.pdf_service import build_medical_record_pdf

router = APIRouter(prefix="/medical-records", tags=["medical-records"])

# Nurse gets read-only access (Module 6: "view patient history, doctor
# instructions, prescriptions, lab results") — never added to the write
# dependency below, so nurses can never create/edit a record.
READ_ROLES = ("admin", "doctor", "nurse", "patient")


def _to_read(record: MedicalRecord) -> MedicalRecordRead:
    return MedicalRecordRead(
        id=record.id,
        patient_id=record.patient_id,
        doctor_id=record.doctor_id,
        appointment_id=record.appointment_id,
        symptoms=record.encrypted_symptoms,
        diagnosis=record.encrypted_diagnosis,
        notes=record.encrypted_notes,
        treatment_plan=record.encrypted_treatment_plan,
        follow_up_date=record.follow_up_date,
        ml_dengue_predicted=record.ml_dengue_predicted,
        ml_dengue_probability=record.ml_dengue_probability,
        created_at=record.created_at,
    )


@router.post("", response_model=MedicalRecordRead, dependencies=[Depends(require_role("admin", "doctor"))])
async def create_medical_record(
    payload: MedicalRecordCreate,
    repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    appointment_repo: AppointmentRepository = Depends(get_appointment_repository),
    current_user: User = Depends(get_current_user),
):
    if not await patient_repo.get(payload.patient_id):
        raise NotFoundError("Patient not found")
    if payload.appointment_id is not None and not await appointment_repo.get(payload.appointment_id):
        raise NotFoundError("Appointment not found")

    # A doctor's own doctor_id always wins over whatever the payload says —
    # otherwise a self-authored record with no linked appointment would be
    # invisible to list_for_doctor() (doctor-scoped visibility depends on
    # this field being set). Admin may still specify any doctor_id.
    doctor_id = payload.doctor_id
    if current_user.role == "doctor":
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        doctor_id = doctor.id if doctor else None
    elif payload.doctor_id is not None and not await doctor_repo.get(payload.doctor_id):
        raise NotFoundError("Doctor not found")

    record = MedicalRecord(
        patient_id=payload.patient_id,
        doctor_id=doctor_id,
        appointment_id=payload.appointment_id,
        encrypted_symptoms=payload.symptoms,
        encrypted_diagnosis=payload.diagnosis,
        encrypted_notes=payload.notes,
        encrypted_treatment_plan=payload.treatment_plan,
        follow_up_date=payload.follow_up_date,
    )
    repo.add(record)
    await repo.commit()
    await repo.refresh(record)
    return _to_read(record)


@router.get("", response_model=list[MedicalRecordRead], dependencies=[Depends(require_role(*READ_ROLES))])
async def list_medical_records(
    repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
    patient_id: int | None = None,
    doctor_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    diagnosis: str | None = None,
):
    # date_to is inclusive of the whole day on the frontend's terms, so the
    # repository's `< date_to` bound needs the *next* day's midnight.
    from_dt = datetime.combine(date_from, time.min) if date_from else None
    to_dt = datetime.combine(date_to + timedelta(days=1), time.min) if date_to else None

    if current_user.role == "patient":
        patient = await patient_repo.get_by_user_id(current_user.id)
        records = await repo.list_filtered(
            patient_id=patient.id if patient else -1, doctor_id=doctor_id, date_from=from_dt, date_to=to_dt
        )
    elif current_user.role == "doctor":
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        records = await repo.list_for_doctor(doctor.id if doctor else -1)
        if patient_id:
            records = [r for r in records if r.patient_id == patient_id]
        if from_dt is not None:
            records = [r for r in records if r.created_at >= from_dt]
        if to_dt is not None:
            records = [r for r in records if r.created_at < to_dt]
    else:
        # admin / nurse
        records = await repo.list_filtered(patient_id=patient_id, doctor_id=doctor_id, date_from=from_dt, date_to=to_dt)

    if diagnosis:
        # encrypted_diagnosis can't be filtered in SQL (see repository
        # docstring) — matched here in Python against the already-decrypted
        # value instead, after the DB-level filters above narrowed the set.
        needle = diagnosis.lower()
        records = [r for r in records if r.encrypted_diagnosis and needle in r.encrypted_diagnosis.lower()]

    return [_to_read(r) for r in records]


@router.get("/{record_id}/pdf", dependencies=[Depends(require_role(*READ_ROLES))])
async def download_medical_record_pdf(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    repo: MedicalRecordRepository = Depends(get_medical_record_repository),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    doctor_repo: DoctorRepository = Depends(get_doctor_repository),
    current_user: User = Depends(get_current_user),
):
    record = await repo.get(record_id)
    if not record:
        raise NotFoundError("Medical record not found")
    patient = await patient_repo.get(record.patient_id)

    if current_user.role == "patient" and (not patient or patient.user_id != current_user.id):
        raise ForbiddenError("Not authorized to view this medical record")
    if current_user.role == "doctor":
        doctor = await doctor_repo.get_by_user_id(current_user.id)
        allowed_ids = await doctor_patient_ids(db, doctor.id if doctor else -1)
        if record.patient_id not in allowed_ids:
            raise ForbiddenError("Not authorized to view this medical record")

    doctor_name = "—"
    if record.doctor_id:
        record_doctor = await db.get(Doctor, record.doctor_id)
        doctor_name = record_doctor.full_name if record_doctor else "—"

    pdf_bytes = build_medical_record_pdf(
        {
            "id": record.id,
            "symptoms": record.encrypted_symptoms,
            "diagnosis": record.encrypted_diagnosis,
            "notes": record.encrypted_notes,
            "treatment_plan": record.encrypted_treatment_plan,
            "follow_up_date": record.follow_up_date.isoformat() if record.follow_up_date else None,
            "created_at": record.created_at.isoformat() if record.created_at else "",
            "ml_dengue_predicted": record.ml_dengue_predicted,
            "ml_dengue_probability": record.ml_dengue_probability,
        },
        patient.full_name if patient else "Unknown",
        doctor_name,
        datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="medical_record_{record.id}.pdf"'},
    )
