from app.models.prescription import Prescription, PrescriptionItem
from app.repositories.prescription_repository import PrescriptionRepository
from app.services.audit_service import AuditService


class PrescriptionService:
    def __init__(self, prescription_repo: PrescriptionRepository, audit_service: AuditService):
        self.prescription_repo = prescription_repo
        self.audit_service = audit_service

    async def create_with_items(
        self,
        patient_id: int,
        doctor_id: int,
        medical_record_id: int | None,
        items: list[dict],
        actor_user_id: int,
    ) -> Prescription:
        prescription = Prescription(patient_id=patient_id, doctor_id=doctor_id, medical_record_id=medical_record_id)
        self.prescription_repo.add(prescription)
        await self.prescription_repo.flush()

        for item in items:
            self.prescription_repo.add(PrescriptionItem(prescription_id=prescription.id, **item))

        await self.audit_service.record(actor_user_id, "created_prescription", "prescription", prescription.id)
        await self.prescription_repo.commit()

        return await self.prescription_repo.get_with_items(prescription.id)

    async def list_filtered(self, patient_id: int | None = None) -> list[Prescription]:
        return await self.prescription_repo.list_filtered(patient_id)

    async def get_with_items(self, prescription_id: int) -> Prescription | None:
        return await self.prescription_repo.get_with_items(prescription_id)
