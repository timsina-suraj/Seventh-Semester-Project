from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.lab_test import LabTest
from app.repositories.base import BaseRepository


class LabTestRepository(BaseRepository[LabTest]):
    model = LabTest

    async def get_with_result(self, id_: int) -> LabTest | None:
        # select() rather than Session.get() — same identity-map caveat as
        # PrescriptionRepository.get_with_items().
        result = await self.db.execute(
            select(LabTest).options(selectinload(LabTest.result)).where(LabTest.id == id_)
        )
        return result.scalars().first()

    async def list_filtered(
        self, patient_id: int | None = None, status: str | None = None, search: str | None = None
    ) -> list[LabTest]:
        stmt = select(LabTest).options(selectinload(LabTest.result))
        if patient_id is not None:
            stmt = stmt.where(LabTest.patient_id == patient_id)
        if status is not None:
            stmt = stmt.where(LabTest.status == status)
        if search:
            stmt = stmt.where(LabTest.test_name.ilike(f"%{search}%"))
        stmt = stmt.order_by(LabTest.requested_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
