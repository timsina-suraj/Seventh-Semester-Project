"""End-to-end HTTP tests for Phase C (Document management, PDF generation,
search/filter query params) and Phase D (the ML diagnosis pipeline rewired
onto the new dengue_dataset_withsymptoms.csv schema)."""
from datetime import date, timedelta

import pytest

from app.ml import train_diagnosis
from app.models.admin import Admin
from app.models.doctor import Doctor
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


@pytest.fixture
async def world(db_session, client):
    admin_user = await _create_user(db_session, "admin@phasec.test", "admin")
    db_session.add(Admin(user_id=admin_user.id, name="Phase C Admin"))

    doctor_user = await _create_user(db_session, "doctor@phasec.test", "doctor")
    doctor = Doctor(
        user_id=doctor_user.id, employee_id="DOC-PC01", full_name="Dr. PhaseC", department="General",
        specialization="GP", license_number="LIC-PC01",
    )
    db_session.add(doctor)

    other_doctor_user = await _create_user(db_session, "other-doctor@phasec.test", "doctor")
    other_doctor = Doctor(
        user_id=other_doctor_user.id, employee_id="DOC-PC02", full_name="Dr. Other", department="Cardiology",
        specialization="Cardiologist", license_number="LIC-PC02",
    )
    db_session.add(other_doctor)

    recept_user = await _create_user(db_session, "recept@phasec.test", "receptionist")
    db_session.add(Receptionist(user_id=recept_user.id, employee_id="REC-PC01", full_name="Recept PhaseC"))

    patient_user = await _create_user(db_session, "patient@phasec.test", "patient")
    patient = Patient(
        user_id=patient_user.id, patient_number="PAT-PHASEC-0001", full_name="PhaseC Patient",
        date_of_birth=date(1995, 1, 1), gender="Other", district="Kathmandu",
    )
    db_session.add(patient)

    other_patient_user = await _create_user(db_session, "other-patient@phasec.test", "patient")
    other_patient = Patient(
        user_id=other_patient_user.id, patient_number="PAT-PHASEC-0002", full_name="Other Patient",
        date_of_birth=date(1992, 1, 1), gender="Other", district="Pokhara",
    )
    db_session.add(other_patient)

    await db_session.flush()
    await db_session.commit()

    return {
        "admin": await _login(client, "admin@phasec.test"),
        "doctor": await _login(client, "doctor@phasec.test"),
        "other_doctor": await _login(client, "other-doctor@phasec.test"),
        "receptionist": await _login(client, "recept@phasec.test"),
        "patient": await _login(client, "patient@phasec.test"),
        "other_patient": await _login(client, "other-patient@phasec.test"),
        "doctor_id": doctor.id,
        "patient_id": patient.id,
        "other_patient_id": other_patient.id,
    }


# ── Document management (Module 12) ──────────────────────────────────────────

async def test_document_upload_list_download_and_rbac(client, world, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.document_service.settings.upload_dir", str(tmp_path))

    files = {"file": ("report.txt", b"CBC results: normal", "text/plain")}
    data = {"patient_id": str(world["patient_id"]), "category": "Lab Report"}
    resp = await client.post("/documents", headers=world["admin"], data=data, files=files)
    assert resp.status_code == 201, resp.text
    document = resp.json()
    assert document["original_filename"] == "report.txt"

    # Patient can list and download their own document.
    resp = await client.get("/documents", headers=world["patient"], params={"patient_id": world["patient_id"]})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = await client.get(f"/documents/{document['id']}/download", headers=world["patient"])
    assert resp.status_code == 200
    assert resp.content == b"CBC results: normal"

    # A different patient cannot see or download it.
    resp = await client.get("/documents", headers=world["other_patient"], params={"patient_id": world["patient_id"]})
    assert resp.status_code == 403

    resp = await client.get(f"/documents/{document['id']}/download", headers=world["other_patient"])
    assert resp.status_code == 403

    # A doctor with no relationship to this patient is also blocked.
    resp = await client.get("/documents", headers=world["other_doctor"], params={"patient_id": world["patient_id"]})
    assert resp.status_code == 403

    # Only the uploader (or admin) can delete; the patient themself cannot.
    resp = await client.delete(f"/documents/{document['id']}", headers=world["patient"])
    assert resp.status_code == 403

    resp = await client.delete(f"/documents/{document['id']}", headers=world["admin"])
    assert resp.status_code == 204


async def test_document_upload_rejects_invalid_category(client, world, tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.document_service.settings.upload_dir", str(tmp_path))
    files = {"file": ("x.txt", b"content", "text/plain")}
    data = {"patient_id": str(world["patient_id"]), "category": "Not A Category"}
    resp = await client.post("/documents", headers=world["admin"], data=data, files=files)
    assert resp.status_code == 422


# ── PDF generation (Module 14) ────────────────────────────────────────────────

async def test_medical_record_pdf_download_and_rbac(client, world):
    resp = await client.post(
        "/medical-records", headers=world["doctor"],
        json={"patient_id": world["patient_id"], "symptoms": "Fever", "diagnosis": "Dengue suspected"},
    )
    record_id = resp.json()["id"]

    resp = await client.get(f"/medical-records/{record_id}/pdf", headers=world["patient"])
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")

    resp = await client.get(f"/medical-records/{record_id}/pdf", headers=world["other_patient"])
    assert resp.status_code == 403

    resp = await client.get(f"/medical-records/{record_id}/pdf", headers=world["other_doctor"])
    assert resp.status_code == 403


async def test_prescription_pdf_download(client, world):
    record_resp = await client.post(
        "/medical-records", headers=world["doctor"],
        json={"patient_id": world["patient_id"], "symptoms": "Fever"},
    )
    presc_resp = await client.post(
        "/prescriptions", headers=world["doctor"],
        json={
            "patient_id": world["patient_id"], "medical_record_id": record_resp.json()["id"],
            "items": [{"medicine_name": "Paracetamol", "dosage": "500mg"}],
        },
    )
    prescription_id = presc_resp.json()["id"]

    resp = await client.get(f"/prescriptions/{prescription_id}/pdf", headers=world["admin"])
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


async def test_lab_report_pdf_download(client, world):
    resp = await client.post("/lab-tests", headers=world["doctor"], json={"patient_id": world["patient_id"], "test_name": "CBC"})
    lab_test_id = resp.json()["id"]

    resp = await client.get(f"/lab-tests/{lab_test_id}/pdf", headers=world["patient"])
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


# ── Search / filter query params (Module 15) ──────────────────────────────────

async def test_patient_search_filters_by_name(client, world):
    resp = await client.get("/patients", headers=world["admin"], params={"search": "PhaseC Patient"})
    assert resp.status_code == 200
    names = [p["full_name"] for p in resp.json()]
    assert "PhaseC Patient" in names
    assert "Other Patient" not in names


async def test_doctor_search_and_department_filter(client, world):
    resp = await client.get("/doctors", params={"search": "PhaseC"})
    assert resp.status_code == 200
    assert all("PhaseC" in d["full_name"] for d in resp.json())

    resp = await client.get("/doctors", params={"department": "Cardiology"})
    assert resp.status_code == 200
    assert all(d["department"] == "Cardiology" for d in resp.json())


async def test_pharmacy_search_filters_by_name(client, world):
    await client.post(
        "/pharmacy", headers=world["admin"],
        json={"name": "Amoxicillin 250mg", "unit": "tablets", "stock_quantity": 50, "reorder_threshold": 10},
    )
    await client.post(
        "/pharmacy", headers=world["admin"],
        json={"name": "Ibuprofen 400mg", "unit": "tablets", "stock_quantity": 50, "reorder_threshold": 10},
    )

    resp = await client.get("/pharmacy", headers=world["admin"], params={"search": "Amox"})
    assert resp.status_code == 200
    names = [m["name"] for m in resp.json()]
    assert names == ["Amoxicillin 250mg"]


async def test_appointment_status_and_date_range_filter(client, world):
    monday = date.today() + timedelta(days=(7 - date.today().weekday()) % 7 + 7)
    await client.post(
        f"/doctors/{world['doctor_id']}/availability", headers=world["doctor"],
        json={"day_of_week": monday.weekday(), "start_time": "10:00:00", "end_time": "16:00:00"},
    )
    resp = await client.post(
        "/appointments", headers=world["receptionist"],
        json={"patient_id": world["patient_id"], "doctor_id": world["doctor_id"], "appointment_date": f"{monday.isoformat()}T10:00:00"},
    )
    assert resp.status_code == 200, resp.text

    resp = await client.get("/appointments", headers=world["admin"], params={"status": "Pending"})
    assert resp.status_code == 200
    assert all(a["status"] == "Pending" for a in resp.json())

    resp = await client.get(
        "/appointments", headers=world["admin"],
        params={"date_from": monday.isoformat(), "date_to": monday.isoformat()},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    far_past = (monday - timedelta(days=365)).isoformat()
    resp = await client.get("/appointments", headers=world["admin"], params={"date_from": far_past, "date_to": far_past})
    assert resp.json() == []


async def test_lab_test_search_filters_by_test_name(client, world):
    await client.post("/lab-tests", headers=world["doctor"], json={"patient_id": world["patient_id"], "test_name": "Dengue NS1"})
    await client.post("/lab-tests", headers=world["doctor"], json={"patient_id": world["patient_id"], "test_name": "CBC"})

    resp = await client.get("/lab-tests", headers=world["admin"], params={"search": "Dengue"})
    assert resp.status_code == 200
    assert [t["test_name"] for t in resp.json()] == ["Dengue NS1"]


# ── ML diagnosis pipeline (Phase D) ───────────────────────────────────────────

_DIAGNOSIS_PAYLOAD = {
    "gender": "Female", "age": 28, "district": "Kathmandu", "visit_month": "August",
    "days_since_fever_onset": 3, "body_temperature": 39.2,
    "platelet_day1": 300000, "platelet_day3": 90000,
    "hematocrit_day1": 41.0, "hematocrit_day3": 46.0, "wbc_count": 4200,
    "ns1": True, "igg": False, "igm": True,
    "joint_pain": "Severe", "headache": True, "retro_orbital_pain": True, "myalgia": True, "rash": False,
    "persistent_vomiting": True, "abdominal_pain": True, "bleeding": False,
    "restlessness": False, "lethargy": False, "liver_enlargement": False,
    "previous_dengue_history": False, "diabetes": False, "hypertension": False, "obesity": False, "pregnancy": False,
}


async def test_predict_patient_with_new_schema_returns_severity_and_warning_signs(client, world):
    train_diagnosis.train_and_store()

    resp = await client.post("/ml/predict/patient", headers=world["doctor"], json=_DIAGNOSIS_PAYLOAD)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body["dengue_positive"], bool)
    assert 0.0 <= body["probability"] <= 1.0
    assert body["severity_hint"] in ("Mild", "Moderate", "Severe")
    assert body["warning_sign_count"] == 2  # persistent_vomiting + abdominal_pain


async def test_predict_patient_creates_medical_record_for_given_patient(client, world):
    train_diagnosis.train_and_store()

    resp = await client.post(
        "/ml/predict/patient", headers=world["doctor"],
        json={**_DIAGNOSIS_PAYLOAD, "patient_id": world["patient_id"]},
    )
    assert resp.status_code == 200, resp.text

    resp = await client.get("/medical-records", headers=world["patient"])
    records = resp.json()
    assert any(r["ml_dengue_probability"] is not None for r in records)
