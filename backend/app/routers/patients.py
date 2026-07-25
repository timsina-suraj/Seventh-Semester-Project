from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientCreated, PatientRead, PatientUpdate
from app.security.auth import generate_temp_password, get_current_user, hash_password
from app.security.rbac import require_role

router = APIRouter(prefix="/patients", tags=["patients"])


def _to_read(patient: Patient) -> PatientRead:
    linked_user = patient.user  # relationship added on Patient model
    return PatientRead(
        id=patient.id,
        name=patient.encrypted_name,
        address=patient.encrypted_address,
        phone=patient.encrypted_phone,
        age=patient.age,
        gender=patient.gender,
        district=patient.district,
        created_date=patient.created_date,
        login_email=linked_user.email if linked_user else None,
        must_change_password=linked_user.must_change_password if linked_user else None,
    )


def _get_or_404(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("", response_model=PatientCreated, dependencies=[Depends(require_role("admin", "receptionist"))])
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first() or db.query(User).filter(
        User.username == payload.email
    ).first():
        raise HTTPException(status_code=400, detail="A login with this email already exists")

    # The patient's login is created here too, same as staff accounts:
    # a one-time password is generated server-side, shown to whoever
    # registered them exactly once, and must be changed on first login.
    # Email doubles as the username, so there's only one thing to remember.
    temp_password = generate_temp_password()
    user = User(
        username=payload.email,
        email=payload.email,
        password_hash=hash_password(temp_password),
        role="patient",
        must_change_password=True,
    )
    db.add(user)
    db.flush()  # get user.id without committing yet

    patient = Patient(
        user_id=user.id,
        encrypted_name=payload.name,
        encrypted_address=payload.address,
        encrypted_phone=payload.phone,
        age=payload.age,
        gender=payload.gender,
        district=payload.district,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    db.refresh(user)
    base = _to_read(patient)
    return PatientCreated(**base.model_dump(), temporary_password=temp_password)


@router.get("", response_model=list[PatientRead], dependencies=[Depends(require_role("admin", "doctor", "receptionist"))])
def list_patients(district: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Patient)
    if district:
        query = query.filter(Patient.district == district)
    
    if current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.appointment import Appointment
        from app.models.medical_record import MedicalRecord
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        doctor_id = doctor.id if doctor else -1
        
        query = query.filter(
            Patient.id.in_(
                db.query(Appointment.patient_id).filter(Appointment.doctor_id == doctor_id).union(
                    db.query(MedicalRecord.patient_id).filter(MedicalRecord.doctor_id == doctor_id)
                )
            )
        )
        
    return [_to_read(p) for p in query.all()]


@router.get("/me", response_model=PatientRead)
def get_my_patient_record(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patient accounts have a linked patient record")
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="No patient record is linked to this account yet")
    return _to_read(patient)


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(patient_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    patient = _get_or_404(db, patient_id)
    if current_user.role == "patient" and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this patient")
    
    if current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.appointment import Appointment
        from app.models.medical_record import MedicalRecord
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        doctor_id = doctor.id if doctor else -1
        
        has_access = db.query(Appointment).filter(Appointment.patient_id == patient_id, Appointment.doctor_id == doctor_id).first() or \
                     db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id, MedicalRecord.doctor_id == doctor_id).first()
        if not has_access:
            raise HTTPException(status_code=403, detail="Not authorized to view this patient")
            
    return _to_read(patient)


@router.patch("/{patient_id}", response_model=PatientRead, dependencies=[Depends(require_role("admin", "receptionist"))])
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)):
    patient = _get_or_404(db, patient_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        patient.encrypted_name = data["name"]
    if "address" in data:
        patient.encrypted_address = data["address"]
    if "phone" in data:
        patient.encrypted_phone = data["phone"]
    for field in ("age", "gender", "district"):
        if field in data:
            setattr(patient, field, data[field])
    db.commit()
    db.refresh(patient)
    return _to_read(patient)


@router.delete("/{patient_id}", status_code=204, dependencies=[Depends(require_role("admin"))])
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = _get_or_404(db, patient_id)
    db.delete(patient)
    db.commit()