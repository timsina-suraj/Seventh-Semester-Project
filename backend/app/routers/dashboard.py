from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dashboard import HospitalStats
from app.security.rbac import require_role
from app.services.stats_service import get_hospital_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_role("admin"))])


@router.get("/stats", response_model=HospitalStats)
def hospital_stats(db: Session = Depends(get_db)):
    return get_hospital_stats(db)
