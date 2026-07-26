"""FastAPI Depends()-based dependency injection: builds repositories and
services bound to the current request's AsyncSession. This is the
composition root — routers only ever depend on the `get_*_service`
functions here, never construct repositories/services themselves."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.doctor_availability_repository import DoctorAvailabilityRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.lab_result_repository import LabResultRepository
from app.repositories.lab_test_repository import LabTestRepository
from app.repositories.login_log_repository import LoginLogRepository
from app.repositories.medical_history_repository import MedicalHistoryRepository, PatientConditionRepository
from app.repositories.medical_record_repository import MedicalRecordRepository
from app.repositories.medicine_repository import MedicineRepository
from app.repositories.nurse_repository import MedicineAdministrationRepository, PatientVitalsRepository
from app.repositories.otp_repository import OtpRequestRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.staff_repository import (
    DoctorRepository,
    LabTechnicianRepository,
    NurseRepository,
    ReceptionistRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.doctor_availability_service import DoctorAvailabilityService
from app.services.document_service import DocumentService
from app.services.lab_service import LabService
from app.services.login_log_service import LoginLogService
from app.services.notification_service import NotificationService
from app.services.nurse_service import NurseService
from app.services.otp_service import OtpService
from app.services.pharmacy_service import PharmacyService
from app.services.prescription_service import PrescriptionService
from app.services.registration_service import RegistrationService


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(AuditLogRepository(db))


def get_login_log_service(db: AsyncSession = Depends(get_db)) -> LoginLogService:
    return LoginLogService(LoginLogRepository(db))


def get_otp_service(db: AsyncSession = Depends(get_db)) -> OtpService:
    return OtpService(OtpRequestRepository(db))


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    otp_service: OtpService = Depends(get_otp_service),
    login_log_service: LoginLogService = Depends(get_login_log_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuthService:
    return AuthService(UserRepository(db), otp_service, login_log_service, audit_service)


def get_registration_service(
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> RegistrationService:
    return RegistrationService(
        UserRepository(db),
        DoctorRepository(db),
        NurseRepository(db),
        ReceptionistRepository(db),
        LabTechnicianRepository(db),
        PatientRepository(db),
        audit_service,
    )


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_patient_repository(db: AsyncSession = Depends(get_db)) -> PatientRepository:
    return PatientRepository(db)


def get_doctor_repository(db: AsyncSession = Depends(get_db)) -> DoctorRepository:
    return DoctorRepository(db)


def get_nurse_repository(db: AsyncSession = Depends(get_db)) -> NurseRepository:
    return NurseRepository(db)


def get_receptionist_repository(db: AsyncSession = Depends(get_db)) -> ReceptionistRepository:
    return ReceptionistRepository(db)


def get_lab_technician_repository(db: AsyncSession = Depends(get_db)) -> LabTechnicianRepository:
    return LabTechnicianRepository(db)


def get_medical_record_repository(db: AsyncSession = Depends(get_db)) -> MedicalRecordRepository:
    return MedicalRecordRepository(db)


def get_medical_history_repository(db: AsyncSession = Depends(get_db)) -> MedicalHistoryRepository:
    return MedicalHistoryRepository(db)


def get_patient_condition_repository(db: AsyncSession = Depends(get_db)) -> PatientConditionRepository:
    return PatientConditionRepository(db)


def get_doctor_availability_service(
    db: AsyncSession = Depends(get_db),
) -> DoctorAvailabilityService:
    return DoctorAvailabilityService(DoctorAvailabilityRepository(db), DoctorRepository(db), AppointmentRepository(db))


def get_appointment_repository(db: AsyncSession = Depends(get_db)) -> AppointmentRepository:
    return AppointmentRepository(db)


def get_appointment_service(
    db: AsyncSession = Depends(get_db),
    availability_service: DoctorAvailabilityService = Depends(get_doctor_availability_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> AppointmentService:
    return AppointmentService(AppointmentRepository(db), availability_service, audit_service)


def get_prescription_service(
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> PrescriptionService:
    return PrescriptionService(PrescriptionRepository(db), audit_service)


def get_lab_test_repository(db: AsyncSession = Depends(get_db)) -> LabTestRepository:
    return LabTestRepository(db)


def get_lab_service(
    db: AsyncSession = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> LabService:
    return LabService(LabTestRepository(db), LabResultRepository(db), audit_service)


def get_pharmacy_service(db: AsyncSession = Depends(get_db)) -> PharmacyService:
    return PharmacyService(MedicineRepository(db), InventoryRepository(db))


def get_nurse_service(db: AsyncSession = Depends(get_db)) -> NurseService:
    return NurseService(PatientVitalsRepository(db), MedicineAdministrationRepository(db))


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(DocumentRepository(db))


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(PatientRepository(db))
