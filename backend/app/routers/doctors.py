from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate, DoctorRead, DoctorUpdate
from app.security.rbac import require_role

router = APIRouter(prefix="/doctors", tags=["doctors"])


def _to_read(doctor: Doctor) -> DoctorRead:
    return DoctorRead(
        id=doctor.id,
        full_name=doctor.full_name,
        specialization=doctor.specialization,
        phone=doctor.encrypted_phone,
        is_available=doctor.is_available,
    )


@router.post("", response_model=DoctorRead, dependencies=[Depends(require_role("admin"))])
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    doctor = Doctor(
        full_name=payload.full_name,
        specialization=payload.specialization,
        encrypted_phone=payload.phone,
        is_available=payload.is_available,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return _to_read(doctor)


@router.get("", response_model=list[DoctorRead])
def list_doctors(available_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(Doctor)
    if available_only:
        query = query.filter(Doctor.is_available.is_(True))
    return [_to_read(d) for d in query.all()]


@router.get("/{doctor_id}", response_model=DoctorRead)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return _to_read(doctor)


@router.patch("/{doctor_id}", response_model=DoctorRead, dependencies=[Depends(require_role("admin"))])
def update_doctor(doctor_id: int, payload: DoctorUpdate, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    data = payload.model_dump(exclude_unset=True)
    if "phone" in data:
        doctor.encrypted_phone = data.pop("phone")
    for field, value in data.items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return _to_read(doctor)


@router.delete("/{doctor_id}", status_code=204, dependencies=[Depends(require_role("admin"))])
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    db.delete(doctor)
    db.commit()
