from datetime import date, datetime, timedelta, timezone

from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User
from app.services.stats_service import get_hospital_stats


async def _setup_doctor_and_patient(db_session, suffix, patient_created_at=None):
    doctor_user = User(email=f"doc-stats-{suffix}@example.com", role="doctor")
    db_session.add(doctor_user)
    await db_session.flush()
    doctor = Doctor(
        user_id=doctor_user.id, employee_id=f"DOC-STATS-{suffix}", full_name="Dr. Stats", department="General",
        specialization="GP", license_number=f"LIC-STATS-{suffix}",
    )
    db_session.add(doctor)

    patient_user = User(email=f"pat-stats-{suffix}@example.com", role="patient")
    db_session.add(patient_user)
    await db_session.flush()
    patient = Patient(
        user_id=patient_user.id, patient_number=f"PAT-STATS-{suffix}", full_name="Stats Patient",
        date_of_birth=date(1990, 1, 1), gender="Other", district="Kathmandu",
        created_at=patient_created_at or datetime.now(timezone.utc),
    )
    db_session.add(patient)
    await db_session.flush()
    return doctor, patient


async def test_appointments_trend_counts_by_day_and_zero_fills(db_session):
    doctor, patient = await _setup_doctor_and_patient(db_session, "1")

    today = datetime.now(timezone.utc)
    db_session.add_all([
        Appointment(patient_id=patient.id, doctor_id=doctor.id, appointment_date=today),
        Appointment(patient_id=patient.id, doctor_id=doctor.id, appointment_date=today),
        Appointment(patient_id=patient.id, doctor_id=doctor.id, appointment_date=today - timedelta(days=3)),
    ])
    await db_session.commit()

    stats = await get_hospital_stats(db_session)

    assert len(stats.appointments_trend) == 14
    assert stats.appointments_trend[-1].date == today.date().isoformat()
    assert stats.appointments_trend[-1].count == 2
    assert stats.appointments_trend[-4].count == 1  # today - 3 days
    assert stats.appointments_trend[0].count == 0  # oldest day in the window — zero-filled, not omitted


async def test_registrations_trend_counts_by_day_and_zero_fills(db_session):
    today = datetime.now(timezone.utc)
    await _setup_doctor_and_patient(db_session, "2", patient_created_at=today)
    await _setup_doctor_and_patient(db_session, "3", patient_created_at=today - timedelta(days=10))

    stats = await get_hospital_stats(db_session)

    assert len(stats.registrations_trend) == 30
    assert stats.registrations_trend[-1].date == today.date().isoformat()
    assert stats.registrations_trend[-1].count == 1
    assert stats.registrations_trend[-11].count == 1  # today - 10 days
    assert stats.registrations_trend[0].count == 0  # oldest day in the window — zero-filled, not omitted
