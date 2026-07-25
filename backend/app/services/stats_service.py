from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.lab import LabResult
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.pharmacy import PharmacyItem
from app.schemas.dashboard import HospitalStats


def get_hospital_stats(db: Session) -> HospitalStats:
    total_patients = db.query(Patient).count()
    dengue_cases_flagged = db.query(MedicalRecord).filter(MedicalRecord.ml_dengue_predicted.is_(True)).count()
    available_doctors = db.query(Doctor).filter(Doctor.is_available.is_(True)).count()
    total_appointments = db.query(Appointment).count()
    total_lab_results = db.query(LabResult).count()
    low_stock_items = sum(1 for item in db.query(PharmacyItem).all() if item.is_low_stock)
    open_alerts = db.query(Alert).filter(Alert.status == "open").count()

    return HospitalStats(
        total_patients=total_patients,
        dengue_cases_flagged=dengue_cases_flagged,
        available_doctors=available_doctors,
        total_appointments=total_appointments,
        total_lab_results=total_lab_results,
        low_stock_items=low_stock_items,
        open_alerts=open_alerts,
    )
