from app.core.exceptions import NotFoundError, ValidationError
from app.models.lab_result import LabResult
from app.models.lab_test import LabTest
from app.repositories.lab_result_repository import LabResultRepository
from app.repositories.lab_test_repository import LabTestRepository
from app.services.audit_service import AuditService


class LabService:
    def __init__(
        self,
        lab_test_repo: LabTestRepository,
        lab_result_repo: LabResultRepository,
        audit_service: AuditService,
    ):
        self.lab_test_repo = lab_test_repo
        self.lab_result_repo = lab_result_repo
        self.audit_service = audit_service

    async def request_test(self, patient_id: int, doctor_id: int, test_name: str, actor_user_id: int) -> LabTest:
        lab_test = LabTest(patient_id=patient_id, doctor_id=doctor_id, test_name=test_name, status="Requested")
        self.lab_test_repo.add(lab_test)
        await self.lab_test_repo.commit()
        await self.lab_test_repo.refresh(lab_test)

        await self.audit_service.record(actor_user_id, "requested_lab_test", "lab_test", lab_test.id)
        # get_with_result() rather than the already-refreshed `lab_test` —
        # LabTestRead includes `result`, and refresh() doesn't eager-load
        # relationships (same identity-map caveat as PatientRepository.get()
        # in Phase A: a plain lazy access here would hit MissingGreenlet).
        return await self.lab_test_repo.get_with_result(lab_test.id)

    async def upload_result(
        self, lab_test_id: int, result_value: str | None, result_file: str | None, actor_user_id: int
    ) -> LabTest:
        lab_test = await self.lab_test_repo.get(lab_test_id)
        if not lab_test:
            raise NotFoundError("Lab test not found")
        if lab_test.status == "Cancelled":
            raise ValidationError("Cannot upload a result for a cancelled test")
        if await self.lab_result_repo.get_by_lab_test_id(lab_test_id):
            raise ValidationError("A result has already been uploaded for this test")

        self.lab_result_repo.add(
            LabResult(lab_test_id=lab_test_id, result_value=result_value, result_file=result_file)
        )
        lab_test.status = "Completed"
        await self.lab_test_repo.commit()

        await self.audit_service.record(actor_user_id, "uploaded_lab_result", "lab_test", lab_test_id)
        return await self.lab_test_repo.get_with_result(lab_test_id)

    async def list_filtered(
        self, patient_id: int | None = None, status: str | None = None, search: str | None = None
    ) -> list[LabTest]:
        return await self.lab_test_repo.list_filtered(patient_id, status, search)

    async def get_with_result(self, lab_test_id: int) -> LabTest | None:
        return await self.lab_test_repo.get_with_result(lab_test_id)
