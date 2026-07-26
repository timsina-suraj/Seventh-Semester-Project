from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertRead, AlertUpdate
from app.security.rbac import require_role

router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(require_role("admin", "doctor"))])


@router.get("", response_model=list[AlertRead])
async def list_alerts(status: str | None = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Alert)
    if status:
        stmt = stmt.where(Alert.status == status)
    stmt = stmt.order_by(Alert.date.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.patch("/{alert_id}", response_model=AlertRead)
async def update_alert(alert_id: int, payload: AlertUpdate, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise NotFoundError("Alert not found")
    alert.status = payload.status
    await db.commit()
    await db.refresh(alert)
    return alert
