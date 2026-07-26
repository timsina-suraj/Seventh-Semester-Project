from app.models.medicine_administration import MedicineAdministration
from app.models.patient_vitals import PatientVitals
from app.repositories.nurse_repository import MedicineAdministrationRepository, PatientVitalsRepository


class NurseService:
    def __init__(self, vitals_repo: PatientVitalsRepository, medication_repo: MedicineAdministrationRepository):
        self.vitals_repo = vitals_repo
        self.medication_repo = medication_repo

    async def record_vitals(self, patient_id: int, nurse_id: int, **fields) -> PatientVitals:
        vitals = PatientVitals(patient_id=patient_id, nurse_id=nurse_id, **fields)
        self.vitals_repo.add(vitals)
        await self.vitals_repo.commit()
        await self.vitals_repo.refresh(vitals)
        return vitals

    async def list_vitals(self, patient_id: int) -> list[PatientVitals]:
        return await self.vitals_repo.list_for_patient(patient_id)

    async def record_administration(
        self, patient_id: int, nurse_id: int, medicine: str, dose: str | None
    ) -> MedicineAdministration:
        record = MedicineAdministration(patient_id=patient_id, nurse_id=nurse_id, medicine=medicine, dose=dose)
        self.medication_repo.add(record)
        await self.medication_repo.commit()
        await self.medication_repo.refresh(record)
        return record

    async def list_administrations(self, patient_id: int) -> list[MedicineAdministration]:
        return await self.medication_repo.list_for_patient(patient_id)
