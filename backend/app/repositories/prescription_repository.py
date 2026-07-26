from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.prescription import Prescription
from app.repositories.base import BaseRepository


class PrescriptionRepository(BaseRepository[Prescription]):
    model = Prescription

    async def get_with_items(self, id_: int) -> Prescription | None:
        # select() rather than Session.get() — see PatientRepository.get()
        # in Phase A for why get() silently skips loader options once a row
        # is already in the session's identity map (as it will be right
        # after create_with_items() flushes it in the same request).
        result = await self.db.execute(
            select(Prescription).options(selectinload(Prescription.items)).where(Prescription.id == id_)
        )
        return result.scalars().first()

    async def list_filtered(self, patient_id: int | None = None) -> list[Prescription]:
        stmt = select(Prescription).options(selectinload(Prescription.items))
        if patient_id is not None:
            stmt = stmt.where(Prescription.patient_id == patient_id)
        stmt = stmt.order_by(Prescription.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
