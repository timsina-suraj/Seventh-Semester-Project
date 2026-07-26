from app.models.lab_result import LabResult
from app.repositories.base import BaseRepository


class LabResultRepository(BaseRepository[LabResult]):
    model = LabResult

    async def get_by_lab_test_id(self, lab_test_id: int) -> LabResult | None:
        return await self.get_by(lab_test_id=lab_test_id)
