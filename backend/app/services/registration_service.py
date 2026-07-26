"""Creates User + role-profile rows in one transaction, for both staff
(admin-created) and patients (receptionist-created) — Module 1's two
registration workflows. Both end the same way: registration confirmation
email fired in the background, an audit log entry written, and the account
left inactive with must_change_password=True until the OTP first-login flow
(Module 3) completes."""
import json

from fastapi import BackgroundTasks

from app.core.exceptions import EmailAlreadyExistsError
from app.core.logging import get_logger
from app.models.admin import Admin
from app.models.doctor import Doctor
from app.models.lab_technician import LabTechnician
from app.models.nurse import Nurse
from app.models.patient import Patient
from app.models.receptionist import Receptionist
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.repositories.staff_repository import (
    DoctorRepository,
    LabTechnicianRepository,
    NurseRepository,
    ReceptionistRepository,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import StaffCreate
from app.schemas.patient import PatientCreate
from app.services.audit_service import AuditService
from app.services.email_service import send_registration_email

logger = get_logger(__name__)


class RegistrationService:
    def __init__(
        self,
        user_repo: UserRepository,
        doctor_repo: DoctorRepository,
        nurse_repo: NurseRepository,
        receptionist_repo: ReceptionistRepository,
        lab_tech_repo: LabTechnicianRepository,
        patient_repo: PatientRepository,
        audit_service: AuditService,
    ):
        self.user_repo = user_repo
        self.doctor_repo = doctor_repo
        self.nurse_repo = nurse_repo
        self.receptionist_repo = receptionist_repo
        self.lab_tech_repo = lab_tech_repo
        self.patient_repo = patient_repo
        self.audit_service = audit_service

    async def _create_user(self, email: str, role: str) -> User:
        if await self.user_repo.email_exists(email):
            raise EmailAlreadyExistsError(email)
        user = User(email=email, role=role)  # password_hash=None, is_active=False, must_change_password=True
        self.user_repo.add(user)
        await self.user_repo.flush()
        return user

    def _notify(self, background_tasks: BackgroundTasks | None, email: str) -> None:
        if background_tasks is not None:
            background_tasks.add_task(send_registration_email, email)
        else:
            send_registration_email(email)

    async def create_staff(
        self,
        payload: StaffCreate,
        actor_user_id: int,
        background_tasks: BackgroundTasks | None = None,
        ip_address: str | None = None,
    ) -> User:
        user = await self._create_user(payload.email, payload.role)

        if payload.role == "doctor":
            employee_id = await self.doctor_repo.next_employee_id()
            self.doctor_repo.add(
                Doctor(
                    user_id=user.id,
                    employee_id=employee_id,
                    full_name=payload.full_name,
                    department=payload.department,
                    specialization=payload.specialization,
                    license_number=payload.license_number,
                )
            )
        elif payload.role == "nurse":
            employee_id = await self.nurse_repo.next_employee_id()
            self.nurse_repo.add(
                Nurse(
                    user_id=user.id,
                    employee_id=employee_id,
                    full_name=payload.full_name,
                    department=payload.department,
                    shift=payload.shift,
                )
            )
        elif payload.role == "receptionist":
            employee_id = await self.receptionist_repo.next_employee_id()
            self.receptionist_repo.add(
                Receptionist(user_id=user.id, employee_id=employee_id, full_name=payload.full_name)
            )
        elif payload.role == "lab_technician":
            employee_id = await self.lab_tech_repo.next_employee_id()
            self.lab_tech_repo.add(
                LabTechnician(
                    user_id=user.id,
                    employee_id=employee_id,
                    full_name=payload.full_name,
                    department=payload.department,
                )
            )

        await self.audit_service.record(actor_user_id, "created_staff_account", "user", user.id, ip_address)
        await self.user_repo.commit()
        await self.user_repo.refresh(user)

        logger.info("staff_account_created user_id=%s role=%s", user.id, payload.role)
        self._notify(background_tasks, user.email)
        return user

    async def create_admin(self, email: str, name: str) -> User:
        """Bootstrap only — not exposed over the API. The first admin is
        created during system setup (see scripts/bootstrap_admin.py), not
        by another admin, per spec."""
        user = await self._create_user(email, "admin")
        self.user_repo.add(Admin(user_id=user.id, name=name))
        await self.user_repo.commit()
        await self.user_repo.refresh(user)
        return user

    async def create_patient(
        self,
        payload: PatientCreate,
        actor_user_id: int,
        background_tasks: BackgroundTasks | None = None,
        ip_address: str | None = None,
    ) -> Patient:
        user = await self._create_user(payload.email, "patient")

        patient_number = await self.patient_repo.next_patient_number()
        patient = Patient(
            user_id=user.id,
            patient_number=patient_number,
            full_name=payload.full_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            blood_group=payload.blood_group,
            encrypted_phone=payload.phone,
            encrypted_address=json.dumps({"province": payload.province, "municipality": payload.municipality}),
            district=payload.district,
            encrypted_emergency_contact=payload.emergency_contact,
            allergies=payload.allergies,
        )
        self.patient_repo.add(patient)
        await self.patient_repo.flush()

        await self.audit_service.record(actor_user_id, "registered_patient", "patient", patient.id, ip_address)
        await self.user_repo.commit()
        await self.patient_repo.refresh(patient)

        logger.info("patient_registered user_id=%s patient_number=%s", user.id, patient_number)
        self._notify(background_tasks, user.email)
        return patient
