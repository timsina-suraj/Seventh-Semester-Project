from datetime import date, datetime, time, timedelta, timezone

from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability
from app.models.user import User
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_availability_repository import DoctorAvailabilityRepository
from app.repositories.staff_repository import DoctorRepository
from app.services.doctor_availability_service import DoctorAvailabilityService


async def _make_doctor(db_session) -> Doctor:
    user = User(email="doc-avail@example.com", role="doctor")
    db_session.add(user)
    await db_session.flush()
    doctor = Doctor(
        user_id=user.id, employee_id="DOC-9001", full_name="Dr. Test", department="General",
        specialization="GP", license_number="LIC-9001",
    )
    db_session.add(doctor)
    await db_session.flush()
    return doctor


def _next_monday() -> date:
    d = date.today()
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d


def _build_service(db_session) -> DoctorAvailabilityService:
    return DoctorAvailabilityService(
        DoctorAvailabilityRepository(db_session), DoctorRepository(db_session), AppointmentRepository(db_session)
    )


async def test_no_availability_means_no_open_slots(db_session):
    doctor = await _make_doctor(db_session)
    service = _build_service(db_session)

    slots = await service.available_slots_on(doctor.id, _next_monday())

    assert slots == []


async def test_full_day_availability_produces_stepped_slots(db_session):
    doctor = await _make_doctor(db_session)
    monday = _next_monday()
    db_session.add(DoctorAvailability(doctor_id=doctor.id, day_of_week=0, start_time=time(10, 0), end_time=time(12, 0)))
    await db_session.flush()
    service = _build_service(db_session)

    slots = await service.available_slots_on(doctor.id, monday)

    # 30-minute default step over a 2-hour window -> 4 slots (10:00, 10:30, 11:00, 11:30)
    assert slots == [time(10, 0), time(10, 30), time(11, 0), time(11, 30)]


async def test_booked_slot_is_excluded_from_available_slots(db_session):
    doctor = await _make_doctor(db_session)
    monday = _next_monday()
    db_session.add(DoctorAvailability(doctor_id=doctor.id, day_of_week=0, start_time=time(10, 0), end_time=time(11, 0)))
    patient_user = User(email="pat-avail@example.com", role="patient")
    db_session.add(patient_user)
    await db_session.flush()

    from app.models.patient import Patient

    patient = Patient(
        user_id=patient_user.id, patient_number="PAT-TEST-9001", full_name="Test Patient",
        date_of_birth=date(1990, 1, 1), gender="Other", district="Kathmandu",
    )
    db_session.add(patient)
    await db_session.flush()

    db_session.add(Appointment(
        patient_id=patient.id, doctor_id=doctor.id,
        appointment_date=datetime(monday.year, monday.month, monday.day, 10, 0, tzinfo=timezone.utc),
        status="Pending",
    ))
    await db_session.commit()

    service = _build_service(db_session)
    slots = await service.available_slots_on(doctor.id, monday)

    assert time(10, 0) not in slots
    assert time(10, 30) in slots


async def test_is_within_availability_true_and_false(db_session):
    doctor = await _make_doctor(db_session)
    monday = _next_monday()
    db_session.add(DoctorAvailability(doctor_id=doctor.id, day_of_week=0, start_time=time(10, 0), end_time=time(16, 0)))
    await db_session.commit()
    service = _build_service(db_session)

    inside = datetime(monday.year, monday.month, monday.day, 11, 0, tzinfo=timezone.utc)
    outside = datetime(monday.year, monday.month, monday.day, 8, 0, tzinfo=timezone.utc)

    assert await service.is_within_availability(doctor.id, inside) is True
    assert await service.is_within_availability(doctor.id, outside) is False
