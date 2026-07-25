from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordRead
from app.security.auth import get_current_user
from app.security.rbac import require_role

router = APIRouter(prefix="/medical-records", tags=["medical-records"])


def _to_read(record: MedicalRecord) -> MedicalRecordRead:
    return MedicalRecordRead(
        id=record.id,
        patient_id=record.patient_id,
        doctor_id=record.doctor_id,
        symptoms=record.encrypted_symptoms,
        diagnosis=record.encrypted_diagnosis,
        lab_result=record.encrypted_lab_result,
        prescription=record.encrypted_prescription,
        prescribed_tests=record.encrypted_prescribed_tests,
        medical_history=record.encrypted_medical_history,
        clinical_history=record.encrypted_clinical_history,
        doctor_note=record.encrypted_doctor_note,
        ml_dengue_predicted=record.ml_dengue_predicted,
        ml_dengue_probability=record.ml_dengue_probability,
        date=record.date,
    )


@router.post("", response_model=MedicalRecordRead, dependencies=[Depends(require_role("admin", "doctor"))])
def create_medical_record(payload: MedicalRecordCreate, db: Session = Depends(get_db)):
    record = MedicalRecord(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        encrypted_symptoms=payload.symptoms,
        encrypted_diagnosis=payload.diagnosis,
        encrypted_lab_result=payload.lab_result,
        encrypted_prescription=payload.prescription,
        encrypted_prescribed_tests=payload.prescribed_tests,
        encrypted_medical_history=payload.medical_history,
        encrypted_clinical_history=payload.clinical_history,
        encrypted_doctor_note=payload.doctor_note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _to_read(record)


@router.get("", response_model=list[MedicalRecordRead])
def list_medical_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    patient_id: int | None = None,
):
    query = db.query(MedicalRecord)
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        query = query.filter(MedicalRecord.patient_id == (patient.id if patient else -1))
    elif current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.appointment import Appointment
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        doctor_id = doctor.id if doctor else -1
        
        query = query.filter(
            MedicalRecord.patient_id.in_(
                db.query(Appointment.patient_id).filter(Appointment.doctor_id == doctor_id).union(
                    db.query(MedicalRecord.patient_id).filter(MedicalRecord.doctor_id == doctor_id)
                )
            )
        )
    elif current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if patient_id:
        query = query.filter(MedicalRecord.patient_id == patient_id)
        
    return [_to_read(r) for r in query.order_by(MedicalRecord.date.desc()).all()]
