"""End-to-end tests closing four gaps found against the original module
spec: appointment receipt PDF (Module 14), patient blood-group search and
medical-record doctor/date/diagnosis filters (Module 15), and wiring real
lab_tests/lab_results into the dengue-risk ML pipeline (Module 17)."""
from datetime import date, timedelta

import pytest

from app.ml import train_diagnosis
from app.models.admin import Admin
from app.models.doctor import Doctor
from app.models.patient import Patient
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


@pytest.fixture
async def world(db_session, client):
    admin_user = await _create_user(db_session, "admin@gaps.test", "admin")
    db_session.add(Admin(user_id=admin_user.id, name="Gaps Admin"))

    doctor_user = await _create_user(db_session, "doctor@gaps.test", "doctor")
    doctor = Doctor(
        user_id=doctor_user.id, employee_id="DOC-GP01", full_name="Dr. Gaps", department="General",
        specialization="GP", license_number="LIC-GP01",
    )
    db_session.add(doctor)

    other_doctor_user = await _create_user(db_session, "other-doctor@gaps.test", "doctor")
    other_doctor = Doctor(
        user_id=other_doctor_user.id, employee_id="DOC-GP02", full_name="Dr. Other Gaps", department="Cardiology",
        specialization="Cardiologist", license_number="LIC-GP02",
    )
    db_session.add(other_doctor)

    patient_user = await _create_user(db_session, "patient@gaps.test", "patient")
    patient = Patient(
        user_id=patient_user.id, patient_number="PAT-GAPS-0001", full_name="Gaps Patient",
        date_of_birth=date(1995, 1, 1), gender="Other", district="Kathmandu", blood_group="O+",
    )
    db_session.add(patient)

    other_patient_user = await _create_user(db_session, "other-patient@gaps.test", "patient")
    other_patient = Patient(
        user_id=other_patient_user.id, patient_number="PAT-GAPS-0002", full_name="Other Gaps Patient",
        date_of_birth=date(1992, 1, 1), gender="Other", district="Pokhara", blood_group="AB-",
    )
    db_session.add(other_patient)

    await db_session.flush()
    await db_session.commit()

    return {
        "admin": await _login(client, "admin@gaps.test"),
        "doctor": await _login(client, "doctor@gaps.test"),
        "other_doctor": await _login(client, "other-doctor@gaps.test"),
        "patient": await _login(client, "patient@gaps.test"),
        "other_patient": await _login(client, "other-patient@gaps.test"),
        "doctor_id": doctor.id,
        "other_doctor_id": other_doctor.id,
        "patient_id": patient.id,
        "other_patient_id": other_patient.id,
    }


# ── Module 14: appointment receipt PDF ────────────────────────────────────────

async def _book_appointment(client, world, when):
    await client.post(
        f"/doctors/{world['doctor_id']}/availability", headers=world["doctor"],
        json={"day_of_week": when.weekday(), "start_time": "10:00:00", "end_time": "16:00:00"},
    )
    resp = await client.post(
        "/appointments", headers=world["admin"],
        json={"patient_id": world["patient_id"], "doctor_id": world["doctor_id"], "appointment_date": f"{when.isoformat()}T10:00:00"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _next_matching_weekday(days_ahead_min: int = 7) -> date:
    return date.today() + timedelta(days=days_ahead_min)


async def test_appointment_receipt_pdf_download_and_rbac(client, world):
    when = _next_matching_weekday()
    appointment = await _book_appointment(client, world, when)

    resp = await client.get(f"/appointments/{appointment['id']}/pdf", headers=world["patient"])
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")

    resp = await client.get(f"/appointments/{appointment['id']}/pdf", headers=world["doctor"])
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")

    resp = await client.get(f"/appointments/{appointment['id']}/pdf", headers=world["other_patient"])
    assert resp.status_code == 403

    resp = await client.get(f"/appointments/{appointment['id']}/pdf", headers=world["other_doctor"])
    assert resp.status_code == 403


# ── Module 15: patient blood-group search ─────────────────────────────────────

async def test_patient_list_filters_by_blood_group(client, world):
    resp = await client.get("/patients", headers=world["admin"], params={"blood_group": "O+"})
    assert resp.status_code == 200
    groups = {p["blood_group"] for p in resp.json()}
    names = {p["full_name"] for p in resp.json()}
    assert groups == {"O+"}
    assert "Gaps Patient" in names
    assert "Other Gaps Patient" not in names


# ── Module 15: medical record doctor/date/diagnosis filters ──────────────────

async def test_medical_record_doctor_and_diagnosis_filters(client, world):
    await client.post(
        "/medical-records", headers=world["doctor"],
        json={"patient_id": world["patient_id"], "symptoms": "Fever", "diagnosis": "Dengue suspected"},
    )
    await client.post(
        "/medical-records", headers=world["other_doctor"],
        json={"patient_id": world["patient_id"], "symptoms": "Chest pain", "diagnosis": "Angina"},
    )

    resp = await client.get("/medical-records", headers=world["admin"], params={"doctor_id": world["doctor_id"]})
    assert resp.status_code == 200
    diagnoses = [r["diagnosis"] for r in resp.json()]
    assert diagnoses == ["Dengue suspected"]

    resp = await client.get("/medical-records", headers=world["admin"], params={"diagnosis": "dengue"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["diagnosis"] == "Dengue suspected"

    resp = await client.get("/medical-records", headers=world["admin"], params={"diagnosis": "nonexistent-condition"})
    assert resp.json() == []


async def test_medical_record_date_range_filter(client, world):
    await client.post(
        "/medical-records", headers=world["doctor"],
        json={"patient_id": world["patient_id"], "symptoms": "Fever"},
    )
    # The record's created_at is server-side "now" in UTC; widen the window
    # a day on each side so local-vs-UTC clock skew near a day boundary
    # can't make an otherwise-correct filter look broken.
    window_from = (date.today() - timedelta(days=1)).isoformat()
    window_to = (date.today() + timedelta(days=1)).isoformat()

    resp = await client.get(
        "/medical-records", headers=world["admin"], params={"date_from": window_from, "date_to": window_to}
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    far_past = (date.today() - timedelta(days=365)).isoformat()
    resp = await client.get(
        "/medical-records", headers=world["admin"], params={"date_from": far_past, "date_to": far_past}
    )
    assert resp.json() == []


# ── Module 17: real lab results feed the ML prediction pipeline ──────────────

_BASE_DIAGNOSIS_PAYLOAD = {
    "gender": "Female", "age": 28, "district": "Kathmandu", "visit_month": "August",
    "days_since_fever_onset": 3, "body_temperature": 39.2,
    "platelet_day1": 999999, "platelet_day3": 999999,  # deliberately implausible manual guesses
    "hematocrit_day1": 40.0, "hematocrit_day3": 40.0, "wbc_count": 5000,
    "ns1": False, "igg": False, "igm": False,
    "joint_pain": "No_Joint_Pain", "headache": False, "retro_orbital_pain": False, "myalgia": False, "rash": False,
    "persistent_vomiting": False, "abdominal_pain": False, "bleeding": False,
    "restlessness": False, "lethargy": False, "liver_enlargement": False,
    "previous_dengue_history": False, "diabetes": False, "hypertension": False, "obesity": False, "pregnancy": False,
}


async def test_predict_patient_uses_real_lab_results_over_manual_input(client, world):
    train_diagnosis.train_and_store()

    resp = await client.post(
        "/lab-tests", headers=world["doctor"], json={"patient_id": world["patient_id"], "test_name": "Platelet Count"}
    )
    lab_test_id = resp.json()["id"]
    resp = await client.post(
        f"/lab-tests/{lab_test_id}/result", headers=world["admin"], json={"result_value": "45000 /uL"}
    )
    assert resp.status_code == 200, resp.text

    resp = await client.post(
        "/ml/predict/patient", headers=world["doctor"],
        json={**_BASE_DIAGNOSIS_PAYLOAD, "patient_id": world["patient_id"]},
    )
    assert resp.status_code == 200, resp.text
    # The manual platelet_day1/day3 of 999999 would never trigger "Severe"
    # on its own — a real completed platelet result of 45000 (well under the
    # 50k severe threshold) proves the real lab value was actually used.
    assert resp.json()["severity_hint"] == "Severe"
