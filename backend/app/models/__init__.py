"""Import every model so Base.metadata.create_all() / Alembic autogenerate
picks them all up."""
from app.models.user import User  # noqa: F401
from app.models.otp_request import OtpRequest  # noqa: F401
from app.models.login_log import LoginLog  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.admin import Admin  # noqa: F401
from app.models.doctor import Doctor  # noqa: F401
from app.models.doctor_availability import DoctorAvailability  # noqa: F401
from app.models.nurse import Nurse  # noqa: F401
from app.models.receptionist import Receptionist  # noqa: F401
from app.models.lab_technician import LabTechnician  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.appointment import Appointment  # noqa: F401
from app.models.medical_record import MedicalRecord  # noqa: F401
from app.models.medical_history import MedicalHistory  # noqa: F401
from app.models.patient_conditions import PatientCondition  # noqa: F401
from app.models.prescription import Prescription, PrescriptionItem  # noqa: F401
from app.models.lab_test import LabTest  # noqa: F401
from app.models.lab_result import LabResult  # noqa: F401
from app.models.medicine import Medicine  # noqa: F401
from app.models.inventory import Inventory  # noqa: F401
from app.models.patient_vitals import PatientVitals  # noqa: F401
from app.models.medicine_administration import MedicineAdministration  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.document import Document  # noqa: F401
