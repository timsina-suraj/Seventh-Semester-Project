from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lab import LabResult
from app.schemas.lab import LabResultCreate, LabResultRead
from app.security.rbac import require_role

router = APIRouter(prefix="/lab", tags=["lab"])


@router.post("", response_model=LabResultRead, dependencies=[Depends(require_role("admin", "doctor"))])
def create_lab_result(payload: LabResultCreate, db: Session = Depends(get_db)):
    result = LabResult(**payload.model_dump())
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.get("", response_model=list[LabResultRead], dependencies=[Depends(require_role("admin", "doctor"))])
def list_lab_results(patient_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(LabResult)
    if patient_id:
        query = query.filter(LabResult.patient_id == patient_id)
    return query.order_by(LabResult.recorded_at.desc()).all()


@router.get("/{lab_id}", response_model=LabResultRead, dependencies=[Depends(require_role("admin", "doctor"))])
def get_lab_result(lab_id: int, db: Session = Depends(get_db)):
    result = db.get(LabResult, lab_id)
    if not result:
        raise HTTPException(status_code=404, detail="Lab result not found")
    return result
