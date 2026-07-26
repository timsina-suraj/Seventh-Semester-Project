"""End-to-end HTTP tests for Module 1 (registration) + Module 3 (security):
registration -> confirmation email -> pre-login -> OTP email -> OTP login ->
set initial password -> normal login, plus RBAC boundaries and the
audit/login-log trail those actions are supposed to leave behind."""
import re

import pytest

from app.models.admin import Admin
from app.models.user import User
from app.security.auth import hash_password


@pytest.fixture
def sent_emails(monkeypatch):
    """Captures every outbound email instead of hitting SMTP. Returns a
    list of (kind, to_email, otp_or_none) tuples, appended to as the test
    runs (background tasks execute inline under ASGITransport)."""
    captured = []

    def fake_registration(to_email):
        captured.append(("registration", to_email, None))

    def fake_otp(to_email, otp):
        captured.append(("otp", to_email, otp))

    def fake_reset(to_email, otp):
        captured.append(("reset", to_email, otp))

    monkeypatch.setattr("app.services.registration_service.send_registration_email", fake_registration)
    monkeypatch.setattr("app.services.auth_service.send_otp_email", fake_otp)
    monkeypatch.setattr("app.services.auth_service.send_password_reset_otp_email", fake_reset)
    return captured


@pytest.fixture
async def admin_auth(db_session, client, sent_emails):
    user = User(
        email="admin@example.com",
        role="admin",
        password_hash=hash_password("Admin@12345"),
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(Admin(user_id=user.id, name="Test Admin"))
    await db_session.commit()

    resp = await client.post(
        "/auth/login", data={"username": "admin@example.com", "password": "Admin@12345"}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_full_staff_onboarding_flow(client, admin_auth, sent_emails):
    # 1. Admin creates a nurse account.
    resp = await client.post(
        "/auth/register",
        headers=admin_auth,
        json={
            "email": "nurse.test@example.com",
            "role": "nurse",
            "full_name": "Test Nurse",
            "department": "ICU",
            "shift": "Night",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["is_active"] is False
    assert body["must_change_password"] is True

    # 2. Registration confirmation email fired immediately, separate from OTP.
    assert ("registration", "nurse.test@example.com", None) in sent_emails

    # 3. Attempting a normal login before onboarding is complete must fail
    #    (no password set yet).
    resp = await client.post(
        "/auth/login", data={"username": "nurse.test@example.com", "password": "anything"}
    )
    assert resp.status_code == 401

    # 4. Pre-login detects first-login state and sends an OTP (not the
    #    registration email again).
    resp = await client.post("/auth/pre-login", json={"email": "nurse.test@example.com"})
    assert resp.status_code == 200
    assert resp.json() == {"requires_otp": True, "requires_password": False}
    otp_events = [e for e in sent_emails if e[0] == "otp" and e[1] == "nurse.test@example.com"]
    assert len(otp_events) == 1
    otp_code = otp_events[0][2]
    assert re.fullmatch(r"\d{6}", otp_code)

    # 5. Wrong OTP is rejected.
    resp = await client.post(
        "/auth/login-with-otp", json={"email": "nurse.test@example.com", "otp": "000000"}
    )
    assert resp.status_code == 400

    # 6. Correct OTP logs the user in (still must_change_password=True).
    resp = await client.post(
        "/auth/login-with-otp", json={"email": "nurse.test@example.com", "otp": otp_code}
    )
    assert resp.status_code == 200
    otp_login_body = resp.json()
    assert otp_login_body["must_change_password"] is True
    nurse_headers = {"Authorization": f"Bearer {otp_login_body['access_token']}"}

    # 7. A must-change-password account is blocked from role-gated routes...
    resp = await client.get("/patients", headers=nurse_headers)
    assert resp.status_code == 403

    # ...but can still set its initial password.
    resp = await client.post(
        "/auth/set-initial-password", headers=nurse_headers, json={"new_password": "NursePass@123"}
    )
    assert resp.status_code == 200
    assert resp.json()["must_change_password"] is False

    # 8. Normal login now works with the new password.
    resp = await client.post(
        "/auth/login", data={"username": "nurse.test@example.com", "password": "NursePass@123"}
    )
    assert resp.status_code == 200

    # 9. The whole trail is visible to the admin via the log endpoints.
    resp = await client.get("/audit-logs", headers=admin_auth)
    assert resp.status_code == 200
    actions = {row["action"] for row in resp.json()}
    assert {"created_staff_account", "set_initial_password"} <= actions

    resp = await client.get("/login-logs", headers=admin_auth)
    assert resp.status_code == 200
    statuses = [row["status"] for row in resp.json() if row["attempted_email"] == "nurse.test@example.com"]
    assert "failed" in statuses  # the bad-OTP / no-password attempts
    assert "success" in statuses


async def test_registration_rejects_duplicate_email(client, admin_auth):
    payload = {
        "email": "dup@example.com",
        "role": "receptionist",
        "full_name": "First",
    }
    resp = await client.post("/auth/register", headers=admin_auth, json=payload)
    assert resp.status_code == 201

    resp = await client.post("/auth/register", headers=admin_auth, json=payload)
    assert resp.status_code == 400


async def test_registration_requires_admin_role(client):
    resp = await client.post(
        "/auth/register",
        json={"email": "x@example.com", "role": "doctor", "full_name": "X", "department": "A", "specialization": "B", "license_number": "C"},
    )
    assert resp.status_code == 401  # no token at all


async def test_patient_registration_generates_patient_number(client, admin_auth, sent_emails):
    resp = await client.post(
        "/patients",
        headers=admin_auth,
        json={
            "full_name": "Ram Thapa",
            "email": "ram.thapa@example.com",
            "date_of_birth": "1995-05-10",
            "gender": "Male",
            "blood_group": "O+",
            "district": "Kathmandu",
            "province": "Bagmati",
            "municipality": "Baneshwor",
            "phone": "9800000001",
            "emergency_contact": "9800000002",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert re.fullmatch(r"PAT-\d{4}-\d{4}", body["patient_number"])
    assert body["province"] == "Bagmati"
    assert body["municipality"] == "Baneshwor"
    assert body["district"] == "Kathmandu"
    assert ("registration", "ram.thapa@example.com", None) in sent_emails


async def test_forgot_password_uses_separate_otp_purpose_from_first_login(client, db_session, sent_emails):
    user = User(
        email="reset-me@example.com",
        role="doctor",
        password_hash=hash_password("Original@123"),
        is_active=True,
        must_change_password=False,
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post("/auth/forgot-password", json={"email": "reset-me@example.com"})
    assert resp.status_code == 200
    reset_events = [e for e in sent_emails if e[0] == "reset"]
    assert len(reset_events) == 1
    otp_code = reset_events[0][2]

    resp = await client.post(
        "/auth/reset-password",
        json={"email": "reset-me@example.com", "otp": otp_code, "new_password": "Brand@New1"},
    )
    assert resp.status_code == 200

    resp = await client.post(
        "/auth/login", data={"username": "reset-me@example.com", "password": "Brand@New1"}
    )
    assert resp.status_code == 200
