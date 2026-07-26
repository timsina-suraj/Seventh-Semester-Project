"""End-to-end HTTP tests for Phase E: admin staff-profile management
(GET/PATCH for nurse/receptionist/lab_technician rosters), admin-initiated
password reset, GET /doctors/me, and the prescriptions list doctor-scoping
fix (a doctor should only ever see their own patients' prescriptions)."""
from datetime import date

import pytest
from sqlalchemy import select

from app.models.admin import Admin
from app.models.doctor import Doctor
from app.models.lab_technician import LabTechnician
from app.models.nurse import Nurse
from app.models.patient import Patient
from app.models.receptionist import Receptionist
from app.models.user import User
from app.security.auth import hash_password

PASSWORD = "Password@123"

# Note: ".test" is an IANA-reserved special-use TLD (RFC 6761) that
# email-validator (used by Pydantic's EmailStr, e.g. on UserRead) rejects
# outright — unlike "example.com", which is allowed. Every address here uses
# a ".com"-style domain instead so responses that round-trip through
# EmailStr-validated schemas (like POST /users/{id}/reset-password) don't 422.


async def _create_user(db_session, email, role, must_change_password=False) -> User:
    user = User(
        email=email, role=role, password_hash=hash_password(PASSWORD), is_active=True,
        must_change_password=must_change_password,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def _login(client, email) -> dict:
    resp = await client.post("/auth/login", data={"username": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def world(db_session, client):
    admin_user = await _create_user(db_session, "admin@phasee-e2e.com", "admin")
    db_session.add(Admin(user_id=admin_user.id, name="Phase E Admin"))

    doctor_user = await _create_user(db_session, "doctor@phasee-e2e.com", "doctor")
    doctor = Doctor(
        user_id=doctor_user.id, employee_id="DOC-PE01", full_name="Dr. PhaseE", department="General",
        specialization="GP", license_number="LIC-PE01",
    )
    db_session.add(doctor)

    other_doctor_user = await _create_user(db_session, "other-doctor@phasee-e2e.com", "doctor")
    other_doctor = Doctor(
        user_id=other_doctor_user.id, employee_id="DOC-PE02", full_name="Dr. Other", department="Cardiology",
        specialization="Cardiologist", license_number="LIC-PE02",
    )
    db_session.add(other_doctor)

    nurse_user = await _create_user(db_session, "nurse@phasee-e2e.com", "nurse")
    nurse = Nurse(user_id=nurse_user.id, employee_id="NUR-PE01", full_name="Nurse PhaseE", department="Ward", shift="Morning")
    db_session.add(nurse)

    recept_user = await _create_user(db_session, "recept@phasee-e2e.com", "receptionist")
    receptionist = Receptionist(user_id=recept_user.id, employee_id="REC-PE01", full_name="Recept PhaseE")
    db_session.add(receptionist)

    labtech_user = await _create_user(db_session, "labtech@phasee-e2e.com", "lab_technician")
    lab_technician = LabTechnician(user_id=labtech_user.id, employee_id="LAB-PE01", full_name="LabTech PhaseE", department="Hematology")
    db_session.add(lab_technician)

    patient_user = await _create_user(db_session, "patient@phasee-e2e.com", "patient")
    patient = Patient(
        user_id=patient_user.id, patient_number="PAT-PHASEE-0001", full_name="PhaseE Patient",
        date_of_birth=date(1995, 1, 1), gender="Other", district="Kathmandu",
    )
    db_session.add(patient)

    await db_session.flush()
    await db_session.commit()

    return {
        "admin": await _login(client, "admin@phasee-e2e.com"),
        "doctor": await _login(client, "doctor@phasee-e2e.com"),
        "other_doctor": await _login(client, "other-doctor@phasee-e2e.com"),
        "nurse": await _login(client, "nurse@phasee-e2e.com"),
        "receptionist": await _login(client, "recept@phasee-e2e.com"),
        "lab_technician": await _login(client, "labtech@phasee-e2e.com"),
        "patient": await _login(client, "patient@phasee-e2e.com"),
        "doctor_id": doctor.id,
        "other_doctor_id": other_doctor.id,
        "nurse_id": nurse.id,
        "nurse_user_email": "nurse@phasee-e2e.com",
        "receptionist_id": receptionist.id,
        "lab_technician_id": lab_technician.id,
        "patient_id": patient.id,
        "patient_user_email": "patient@phasee-e2e.com",
    }


# ── Staff profile management (admin only) ─────────────────────────────────────

async def test_admin_can_list_and_update_nurse_profile(client, world):
    resp = await client.get("/nurses", headers=world["admin"])
    assert resp.status_code == 200
    assert any(n["id"] == world["nurse_id"] for n in resp.json())

    resp = await client.patch(
        f"/nurses/{world['nurse_id']}", headers=world["admin"],
        json={"department": "ICU", "shift": "Night"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["department"] == "ICU"
    assert resp.json()["shift"] == "Night"


async def test_admin_can_update_receptionist_and_lab_technician_profiles(client, world):
    resp = await client.patch(
        f"/receptionists/{world['receptionist_id']}", headers=world["admin"], json={"full_name": "Updated Name"}
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"

    resp = await client.patch(
        f"/lab-technicians/{world['lab_technician_id']}", headers=world["admin"], json={"department": "Serology"}
    )
    assert resp.status_code == 200
    assert resp.json()["department"] == "Serology"


async def test_non_admin_cannot_manage_staff_profiles(client, world):
    for role in ("doctor", "nurse", "receptionist", "lab_technician", "patient"):
        resp = await client.get("/nurses", headers=world[role])
        assert resp.status_code == 403, f"{role} should not be able to list nurse profiles"

    resp = await client.patch(f"/nurses/{world['nurse_id']}", headers=world["nurse"], json={"department": "Self-promoted"})
    assert resp.status_code == 403


async def test_update_unknown_profile_id_returns_404(client, world):
    resp = await client.patch("/nurses/999999", headers=world["admin"], json={"department": "Nowhere"})
    assert resp.status_code == 404


# ── Admin-initiated password reset ────────────────────────────────────────────

async def test_admin_reset_password_end_to_end(client, world, db_session):
    result = await db_session.execute(select(User).where(User.email == world["nurse_user_email"]))
    nurse_user_id = result.scalars().first().id

    resp = await client.post(f"/users/{nurse_user_id}/reset-password", headers=world["admin"])
    assert resp.status_code == 200, resp.text
    assert resp.json()["must_change_password"] is True

    # The old password no longer works...
    resp = await client.post("/auth/login", data={"username": world["nurse_user_email"], "password": PASSWORD})
    assert resp.status_code == 401

    # ...and pre-login now routes them through the first-login OTP flow again.
    resp = await client.post("/auth/pre-login", json={"email": world["nurse_user_email"]})
    assert resp.status_code == 200
    assert resp.json()["requires_otp"] is True


async def test_non_admin_cannot_reset_passwords(client, world):
    resp = await client.post(f"/users/1/reset-password", headers=world["doctor"])
    assert resp.status_code == 403


# ── GET /doctors/me ────────────────────────────────────────────────────────────

async def test_doctor_can_resolve_own_profile(client, world):
    resp = await client.get("/doctors/me", headers=world["doctor"])
    assert resp.status_code == 200
    assert resp.json()["id"] == world["doctor_id"]


async def test_non_doctor_cannot_use_doctors_me(client, world):
    resp = await client.get("/doctors/me", headers=world["patient"])
    assert resp.status_code == 403


# ── Prescriptions list is now doctor-scoped ────────────────────────────────────

async def test_prescriptions_list_is_scoped_to_the_doctors_own_patients(client, world):
    record_resp = await client.post(
        "/medical-records", headers=world["doctor"], json={"patient_id": world["patient_id"], "symptoms": "Fever"}
    )
    await client.post(
        "/prescriptions", headers=world["doctor"],
        json={"patient_id": world["patient_id"], "medical_record_id": record_resp.json()["id"], "items": [{"medicine_name": "Paracetamol"}]},
    )

    resp = await client.get("/prescriptions", headers=world["doctor"])
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # A doctor with no relationship to this patient sees nothing.
    resp = await client.get("/prescriptions", headers=world["other_doctor"])
    assert resp.status_code == 200
    assert resp.json() == []

    # Admin and nurse still see everything (unrestricted, unlike doctor).
    resp = await client.get("/prescriptions", headers=world["admin"])
    assert len(resp.json()) == 1
    resp = await client.get("/prescriptions", headers=world["nurse"])
    assert len(resp.json()) == 1
