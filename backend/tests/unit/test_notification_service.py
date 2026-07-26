from datetime import date, datetime, timezone

import pytest

from app.models.doctor import Doctor
from app.models.lab_test import LabTest
from app.models.patient import Patient
from app.models.prescription import Prescription, PrescriptionItem
from app.models.appointment import Appointment
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.services.notification_service import NotificationService


async def _make_patient(db_session, email="notify-target@example.com") -> Patient:
    user = User(email=email, role="patient")
    db_session.add(user)
    await db_session.flush()
    patient = Patient(
        user_id=user.id, patient_number="PAT-NOTIFY-0001", full_name="Notify Patient",
        date_of_birth=date(1990, 1, 1), gender="Other", district="Kathmandu",
    )
    db_session.add(patient)
    await db_session.commit()
    return patient


async def test_notify_appointment_booked_calls_email_with_patient_address(db_session, monkeypatch):
    sent = {}
    monkeypatch.setattr(
        "app.services.notification_service.send_appointment_booked_email",
        lambda to, doctor_name, when, reason: sent.update(to=to, doctor_name=doctor_name),
    )
    patient = await _make_patient(db_session)
    service = NotificationService(PatientRepository(db_session))
    appointment = Appointment(
        patient_id=patient.id, doctor_id=1,
        appointment_date=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc), status="Pending",
    )

    await service.notify_appointment_booked(appointment, "Dr. Test", background_tasks=None)

    assert sent["to"] == "notify-target@example.com"
    assert sent["doctor_name"] == "Dr. Test"


async def test_notify_skips_silently_when_patient_has_no_linked_user_row(db_session, monkeypatch):
    """A dangling patient_id (shouldn't normally happen, but must not crash
    a request just because notification lookup fails)."""
    called = False

    def _record(*args):
        nonlocal called
        called = True

    monkeypatch.setattr("app.services.notification_service.send_lab_result_ready_email", _record)
    service = NotificationService(PatientRepository(db_session))
    lab_test = LabTest(patient_id=999999, doctor_id=1, test_name="CBC", status="Completed")

    await service.notify_lab_result_ready(lab_test, background_tasks=None)

    assert called is False


async def test_notify_prescription_created_includes_item_count(db_session, monkeypatch):
    sent = {}
    monkeypatch.setattr(
        "app.services.notification_service.send_prescription_ready_email",
        lambda to, doctor_name, count: sent.update(to=to, count=count),
    )
    patient = await _make_patient(db_session, "presc-notify@example.com")
    service = NotificationService(PatientRepository(db_session))
    prescription = Prescription(patient_id=patient.id, doctor_id=1)
    prescription.items = [
        PrescriptionItem(medicine_name="Paracetamol"),
        PrescriptionItem(medicine_name="ORS"),
    ]

    await service.notify_prescription_created(prescription, "Dr. Test", background_tasks=None)

    assert sent["to"] == "presc-notify@example.com"
    assert sent["count"] == 2
