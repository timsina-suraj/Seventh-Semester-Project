from sqlalchemy import select

from app.models.medicine_administration import MedicineAdministration
from app.models.patient_vitals import PatientVitals
from app.repositories.base import BaseRepository


class PatientVitalsRepository(BaseRepository[PatientVitals]):
    model = PatientVitals

    async def list_for_patient(self, patient_id: int) -> list[PatientVitals]:
        result = await self.db.execute(
            select(PatientVitals)
            .where(PatientVitals.patient_id == patient_id)
            .order_by(PatientVitals.recorded_at.desc())
        )
        return list(result.scalars().all())


class MedicineAdministrationRepository(BaseRepository[MedicineAdministration]):
    model = MedicineAdministration

    async def list_for_patient(self, patient_id: int) -> list[MedicineAdministration]:
        result = await self.db.execute(
            select(MedicineAdministration)
            .where(MedicineAdministration.patient_id == patient_id)
            .order_by(MedicineAdministration.time_given.desc())
        )
        return list(result.scalars().all())
