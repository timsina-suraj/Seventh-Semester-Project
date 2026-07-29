from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.dashboard import HospitalStats
from app.security.rbac import require_role
from app.services.stats_service import get_hospital_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_role("admin", "doctor"))])


@router.get("/stats", response_model=HospitalStats)
async def hospital_stats(db: AsyncSession = Depends(get_db)):
    return await get_hospital_stats(db)
