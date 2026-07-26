"""End-to-end HTTP tests for Phase B: doctor availability + appointment
conflict validation, EMR + Prescriptions, Lab request/result, Pharmacy
split, and RBAC boundaries for the new Nurse / Lab Technician endpoints."""
from datetime import date, timedelta

import pytest

from app.models.admin import Admin
from app.models.doctor import Doctor
from app.models.lab_technician import LabTechnician
from app.models.nurse import Nurse
from app.models.patient import Patient
from app.models.receptionist import Receptionist
from app.models.user import User
from app.security.auth import hash_password

PASSWORD = "Password@123"


async def _create_user(db_session, email, role) -> User:
    user = User(email=email, role=role, password_hash=hash_password(PASSWORD), is_active=True, must_change_password=False)
    db_session.add(user)
    await db_session.flush()
    return user


async def _login(client, email) -> dict:
    resp = await client.post("/auth/login", data={"username": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _next_monday() -> date:
    d = date.today()
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d + timedelta(days=7)  # a Monday safely in the future


@pytest.fixture
async def world(db_session, client):
    """A fully-populated cast: admin, doctor (no availability yet),
    receptionist, nurse, lab technician, and one patient."""
    admin_user = await _create_user(db_session, "admin@world.test", "admin")
    db_session.add(Admin(user_id=admin_user.id, name="World Admin"))

    doctor_user = await _create_user(db_session, "doctor@world.test", "doctor")
    doctor = Doctor(
        user_id=doctor_user.id, employee_id="DOC-W001", full_name="Dr. World", department="General",
        specialization="GP", license_number="LIC-W001",
    )
    db_session.add(doctor)

    recept_user = await _create_user(db_session, "recept@world.test", "receptionist")
    db_session.add(Receptionist(user_id=recept_user.id, employee_id="REC-W001", full_name="Recept World"))

    nurse_user = await _create_user(db_session, "nurse@world.test", "nurse")
    nurse = Nurse(user_id=nurse_user.id, employee_id="NUR-W001", full_name="Nurse World", department="Ward", shift="Morning")
    db_session.add(nurse)

    labtech_user = await _create_user(db_session, "labtech@world.test", "lab_technician")
    db_session.add(LabTechnician(user_id=labtech_user.id, employee_id="LAB-W001", full_name="LabTech World", department="Hematology"))

    patient_user = await _create_user(db_session, "patient@world.test", "patient")
    patient = Patient(
        user_id=patient_user.id, patient_number="PAT-WORLD-0001", full_name="World Patient",
        date_of_birth=date(1995, 1, 1), gender="Other", district="Kathmandu",
    )
    db_session.add(patient)

    await db_session.flush()
    await db_session.commit()

    return {
        "admin": await _login(client, "admin@world.test"),
        "doctor": await _login(client, "doctor@world.test"),
        "receptionist": await _login(client, "recept@world.test"),
        "nurse": await _login(client, "nurse@world.test"),
        "lab_technician": await _login(client, "labtech@world.test"),
        "patient": await _login(client, "patient@world.test"),
        "doctor_id": doctor.id,
        "patient_id": patient.id,
    }


# ── Doctor availability + appointment conflict validation ──────────────────────

async def test_booking_within_and_outside_availability(client, world):
    monday = _next_monday()
    resp = await client.post(
        f"/doctors/{world['doctor_id']}/availability",
        headers=world["doctor"],
        json={"day_of_week": 0, "start_time": "10:00:00", "end_time": "16:00:00"},
    )
    assert resp.status_code == 201, resp.text

    when = f"{monday.isoformat()}T10:00:00"
    resp = await client.post(
        "/appointments",
        headers=world["receptionist"],
        json={"patient_id": world["patient_id"], "doctor_id": world["doctor_id"], "appointment_date": when, "reason": "Checkup"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "Pending"

    # Same slot again -> rejected (overlap)
    resp = await client.post(
        "/appointments",
        headers=world["receptionist"],
        json={"patient_id": world["patient_id"], "doctor_id": world["doctor_id"], "appointment_date": when, "reason": "Dup"},
    )
    assert resp.status_code == 422

    # Outside declared hours -> rejected
    outside = f"{monday.isoformat()}T08:00:00"
    resp = await client.post(
        "/appointments",
        headers=world["receptionist"],
        json={"patient_id": world["patient_id"], "doctor_id": world["doctor_id"], "appointment_date": outside, "reason": "Too early"},
    )
    assert resp.status_code == 422


async def test_available_slots_excludes_booked_time(client, world):
    monday = _next_monday()
    await client.post(
        f"/doctors/{world['doctor_id']}/availability",
        headers=world["doctor"],
        json={"day_of_week": 0, "start_time": "10:00:00", "end_time": "12:00:00"},
    )
    when = f"{monday.isoformat()}T10:00:00"
    await client.post(
        "/appointments",
        headers=world["receptionist"],
        json={"patient_id": world["patient_id"], "doctor_id": world["doctor_id"], "appointment_date": when},
    )

    resp = await client.get(f"/doctors/{world['doctor_id']}/available-slots", params={"date": monday.isoformat()})
    assert resp.status_code == 200
    times = resp.json()["available_times"]
    assert "10:00:00" not in times
    assert "10:30:00" in times


# ── EMR + Prescriptions ─────────────────────────────────────────────────────────

async def test_emr_and_prescription_flow_with_nurse_read_only_access(client, world):
    resp = await client.post(
        "/medical-records",
        headers=world["doctor"],
        json={"patient_id": world["patient_id"], "symptoms": "Fever", "diagnosis": "Dengue suspected"},
    )
    assert resp.status_code == 200, resp.text
    record = resp.json()
    assert record["doctor_id"] is not None  # auto-derived from the acting doctor

    resp = await client.post(
        "/prescriptions",
        headers=world["doctor"],
        json={
            "patient_id": world["patient_id"],
            "medical_record_id": record["id"],
            "items": [{"medicine_name": "Paracetamol", "dosage": "500mg", "frequency": "3x/day", "duration": "5 days"}],
        },
    )
    assert resp.status_code == 200, resp.text
    prescription = resp.json()
    assert len(prescription["items"]) == 1

    # Patient can read their own record + prescription.
    resp = await client.get("/medical-records", headers=world["patient"])
    assert resp.status_code == 200
    assert any(r["id"] == record["id"] for r in resp.json())

    resp = await client.get("/prescriptions", headers=world["patient"])
    assert resp.status_code == 200
    assert any(p["id"] == prescription["id"] for p in resp.json())

    # Nurse can read but not write.
    resp = await client.get("/medical-records", headers=world["nurse"], params={"patient_id": world["patient_id"]})
    assert resp.status_code == 200

    resp = await client.post(
        "/medical-records", headers=world["nurse"], json={"patient_id": world["patient_id"], "symptoms": "x"}
    )
    assert resp.status_code == 403

    resp = await client.post(
        "/prescriptions",
        headers=world["nurse"],
        json={"patient_id": world["patient_id"], "items": [{"medicine_name": "x"}]},
    )
    assert resp.status_code == 403


# ── Lab request / result ────────────────────────────────────────────────────────

async def test_lab_test_request_and_result_upload(client, world):
    resp = await client.post("/lab-tests", headers=world["doctor"], json={"patient_id": world["patient_id"], "test_name": "CBC"})
    assert resp.status_code == 200, resp.text
    lab_test = resp.json()
    assert lab_test["status"] == "Requested"

    # Receptionist cannot upload a result.
    resp = await client.post(f"/lab-tests/{lab_test['id']}/result", headers=world["receptionist"], json={"result_value": "x"})
    assert resp.status_code == 403

    resp = await client.post(f"/lab-tests/{lab_test['id']}/result", headers=world["lab_technician"], json={"result_value": "Positive"})
    assert resp.status_code == 200, resp.text
    updated = resp.json()
    assert updated["status"] == "Completed"
    assert updated["result"]["result_value"] == "Positive"

    # Doctor and patient can both see the completed result.
    resp = await client.get("/lab-tests", headers=world["doctor"], params={"patient_id": world["patient_id"]})
    assert any(t["id"] == lab_test["id"] and t["result"] for t in resp.json())

    resp = await client.get("/lab-tests", headers=world["patient"])
    assert any(t["id"] == lab_test["id"] and t["result"] for t in resp.json())


# ── Pharmacy split ──────────────────────────────────────────────────────────────

async def test_pharmacy_create_and_low_stock_flag(client, world):
    resp = await client.post(
        "/pharmacy",
        headers=world["admin"],
        json={"name": "Test Medicine", "unit": "tablets", "stock_quantity": 100, "reorder_threshold": 20},
    )
    assert resp.status_code == 200, resp.text
    medicine = resp.json()
    assert medicine["is_low_stock"] is False

    resp = await client.patch(f"/pharmacy/{medicine['id']}", headers=world["admin"], json={"stock_quantity": 5})
    assert resp.status_code == 200
    assert resp.json()["is_low_stock"] is True


# ── RBAC sweep for new Nurse / Lab Technician endpoints ─────────────────────────

async def test_nurse_endpoints_reject_non_nurse_roles(client, world):
    for role in ("admin", "doctor", "receptionist", "lab_technician", "patient"):
        resp = await client.post(
            "/patient-vitals", headers=world[role], json={"patient_id": world["patient_id"], "temperature": 37.0}
        )
        assert resp.status_code == 403, f"{role} should not be able to record vitals"


async def test_lab_result_upload_rejects_non_lab_technician_roles(client, world):
    resp = await client.post("/lab-tests", headers=world["doctor"], json={"patient_id": world["patient_id"], "test_name": "NS1"})
    lab_test_id = resp.json()["id"]

    for role in ("doctor", "receptionist", "nurse", "patient"):
        resp = await client.post(f"/lab-tests/{lab_test_id}/result", headers=world[role], json={"result_value": "x"})
        assert resp.status_code == 403, f"{role} should not be able to upload a lab result"
