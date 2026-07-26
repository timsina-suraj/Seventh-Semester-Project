from app.models.medical_history import MedicalHistory
from app.models.patient_conditions import PatientCondition
from app.repositories.base import BaseRepository


class MedicalHistoryRepository(BaseRepository[MedicalHistory]):
    model = MedicalHistory

    async def list_for_patient(self, patient_id: int) -> list[MedicalHistory]:
        return await self.list(patient_id=patient_id)


class PatientConditionRepository(BaseRepository[PatientCondition]):
    model = PatientCondition

    async def list_for_patient(self, patient_id: int) -> list[PatientCondition]:
        return await self.list(patient_id=patient_id)
