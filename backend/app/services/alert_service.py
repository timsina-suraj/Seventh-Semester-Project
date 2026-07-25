from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.services.risk_classifier import is_high_risk


def create_district_alert(db: Session, district: str, predicted_cases: float, risk_level: str) -> Alert | None:
    """Creates a HIGH RISK district alert (per spec 5.5) if the risk level
    warrants it. Returns None if no alert was needed."""
    if not is_high_risk(risk_level):
        return None

    message = (
        f"HIGH RISK ALERT\n\nDistrict: {district}\nPredicted Cases: {predicted_cases:.0f}\n"
        f"Risk: {risk_level}\n\nAction: Increase dengue preparedness"
    )
    alert = Alert(
        alert_type="district_risk",
        district=district,
        risk_level=risk_level,
        message=message,
        status="open",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def create_patient_diagnosis_alert(db: Session, district: str | None, severity: str, patient_id: int) -> Alert:
    """Creates a NEW DENGUE CASE DETECTED alert (per spec 5.5)."""
    message = (
        f"NEW DENGUE CASE DETECTED\n\nPatient ID: {patient_id}\nDistrict: {district or 'Unknown'}\n"
        f"Severity: {severity}\n\nAction: Doctor monitoring required"
    )
    alert = Alert(
        alert_type="patient_diagnosis",
        district=district,
        risk_level=severity,
        message=message,
        status="open",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
