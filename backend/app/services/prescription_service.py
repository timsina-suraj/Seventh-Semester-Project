from app.core.exceptions import NotFoundError, ValidationError
from app.models.prescription import Prescription, PrescriptionItem
from app.repositories.medicine_repository import MedicineRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.services.audit_service import AuditService


class PrescriptionService:
    def __init__(
        self,
        prescription_repo: PrescriptionRepository,
        medicine_repo: MedicineRepository,
        audit_service: AuditService,
    ):
        self.prescription_repo = prescription_repo
        self.medicine_repo = medicine_repo
        self.audit_service = audit_service

    async def create_with_items(
        self,
        patient_id: int,
        doctor_id: int,
        medical_record_id: int | None,
        items: list[dict],
        actor_user_id: int,
    ) -> Prescription:
        # Aggregate requested quantity per medicine across this prescription
        # (two items can reference the same medicine_id) and validate stock
        # for every referenced medicine BEFORE creating anything, so an
        # insufficient-stock error never leaves a partial prescription saved.
        needed: dict[int, int] = {}
        for item in items:
            medicine_id = item.get("medicine_id")
            if medicine_id is not None:
                needed[medicine_id] = needed.get(medicine_id, 0) + item["quantity"]

        medicines = {}
        for medicine_id, quantity in needed.items():
            medicine = await self.medicine_repo.get_with_inventory(medicine_id)
            if not medicine:
                raise NotFoundError(f"Medicine {medicine_id} not found")
            available = medicine.inventory.quantity if medicine.inventory else 0
            if available < quantity:
                raise ValidationError(
                    f"Insufficient stock for {medicine.name}: available {available}, requested {quantity}"
                )
            medicines[medicine_id] = medicine

        prescription = Prescription(patient_id=patient_id, doctor_id=doctor_id, medical_record_id=medical_record_id)
        self.prescription_repo.add(prescription)
        await self.prescription_repo.flush()

        for item in items:
            self.prescription_repo.add(PrescriptionItem(prescription_id=prescription.id, **item))

        for medicine_id, quantity in needed.items():
            medicines[medicine_id].inventory.quantity -= quantity

        await self.audit_service.record(actor_user_id, "created_prescription", "prescription", prescription.id)
        await self.prescription_repo.commit()

        return await self.prescription_repo.get_with_items(prescription.id)

    async def list_filtered(self, patient_id: int | None = None) -> list[Prescription]:
        return await self.prescription_repo.list_filtered(patient_id)

    async def get_with_items(self, prescription_id: int) -> Prescription | None:
        return await self.prescription_repo.get_with_items(prescription_id)
