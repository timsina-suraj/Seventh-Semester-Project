from datetime import date, datetime, time, timedelta, timezone

import pytest

from app.core.exceptions import ValidationError
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability
from app.models.patient import Patient
from app.models.user import User
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.doctor_availability_repository import DoctorAvailabilityRepository
from app.repositories.staff_repository import DoctorRepository
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.services.doctor_availability_service import DoctorAvailabilityService


def _next_monday() -> date:
    d = date.today()
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d


async def _setup(db_session):
    doctor_user = User(email="doc-book@example.com", role="doctor")
    db_session.add(doctor_user)
    await db_session.flush()
    doctor = Doctor(
        user_id=doctor_user.id, employee_id="DOC-9002", full_name="Dr. Book", department="General",
        specialization="GP", license_number="LIC-9002",
    )
    db_session.add(doctor)
    await db_session.flush()

    monday = _next_monday()
    db_session.add(DoctorAvailability(doctor_id=doctor.id, day_of_week=0, start_time=time(10, 0), end_time=time(16, 0)))

    patient_user = User(email="pat-book@example.com", role="patient")
    db_session.add(patient_user)
    await db_session.flush()
    patient = Patient(
        user_id=patient_user.id, patient_number="PAT-TEST-9002", full_name="Test Patient",
        date_of_birth=date(1990, 1, 1), gender="Other", district="Kathmandu",
    )
    db_session.add(patient)
    await db_session.commit()

    availability_service = DoctorAvailabilityService(
        DoctorAvailabilityRepository(db_session), DoctorRepository(db_session), AppointmentRepository(db_session)
    )
    audit_service = AuditService(AuditLogRepository(db_session))
    appointment_service = AppointmentService(AppointmentRepository(db_session), availability_service, audit_service)
    return appointment_service, doctor, patient, monday, doctor_user


async def test_book_succeeds_within_availability(db_session):
    service, doctor, patient, monday, doctor_user = await _setup(db_session)
    when = datetime(monday.year, monday.month, monday.day, 10, 0, tzinfo=timezone.utc)

    appointment = await service.book(patient.id, doctor.id, when, "Checkup", doctor_user.id)

    assert appointment.status == "Pending"
    # The service normalizes to naive UTC before storing (SQLite drops
    # tzinfo on round-trip anyway) — compare against that, not the
    # originally-aware `when`.
    assert appointment.appointment_date == when.replace(tzinfo=None)


async def test_book_rejects_outside_availability(db_session):
    service, doctor, patient, monday, doctor_user = await _setup(db_session)
    when = datetime(monday.year, monday.month, monday.day, 8, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        await service.book(patient.id, doctor.id, when, None, doctor_user.id)


async def test_book_rejects_overlapping_booking(db_session):
    service, doctor, patient, monday, doctor_user = await _setup(db_session)
    when = datetime(monday.year, monday.month, monday.day, 10, 0, tzinfo=timezone.utc)
    await service.book(patient.id, doctor.id, when, None, doctor_user.id)

    with pytest.raises(ValidationError):
        await service.book(patient.id, doctor.id, when, None, doctor_user.id)


async def test_book_allows_back_to_back_non_overlapping_slots(db_session):
    service, doctor, patient, monday, doctor_user = await _setup(db_session)
    first = datetime(monday.year, monday.month, monday.day, 10, 0, tzinfo=timezone.utc)
    second = first + timedelta(minutes=30)  # exactly one slot-length later — no overlap

    await service.book(patient.id, doctor.id, first, None, doctor_user.id)
    appointment = await service.book(patient.id, doctor.id, second, None, doctor_user.id)

    assert appointment.appointment_date == second.replace(tzinfo=None)


async def test_update_status_rejects_invalid_status(db_session):
    service, doctor, patient, monday, doctor_user = await _setup(db_session)
    when = datetime(monday.year, monday.month, monday.day, 10, 0, tzinfo=timezone.utc)
    appointment = await service.book(patient.id, doctor.id, when, None, doctor_user.id)

    with pytest.raises(ValidationError):
        await service.update_status(appointment.id, "NotARealStatus", doctor_user.id)


async def test_update_status_transitions_to_completed(db_session):
    service, doctor, patient, monday, doctor_user = await _setup(db_session)
    when = datetime(monday.year, monday.month, monday.day, 10, 0, tzinfo=timezone.utc)
    appointment = await service.book(patient.id, doctor.id, when, None, doctor_user.id)

    updated = await service.update_status(appointment.id, "Completed", doctor_user.id)

    assert updated.status == "Completed"
