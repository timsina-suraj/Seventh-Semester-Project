"""Import every model so Base.metadata.create_all() picks them all up."""
from app.models.user import User  # noqa: F401
from app.models.patient import Patient  # noqa: F401
from app.models.doctor import Doctor  # noqa: F401
from app.models.appointment import Appointment  # noqa: F401
from app.models.medical_record import MedicalRecord  # noqa: F401
from app.models.lab import LabResult  # noqa: F401
from app.models.pharmacy import PharmacyItem  # noqa: F401
from app.models.alert import Alert  # noqa: F401
