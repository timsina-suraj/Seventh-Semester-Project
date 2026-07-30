# Admin Dashboard Activity Charts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the admin dashboard's "System Status" card (mostly hardcoded, fake status rows) with two real recharts trend charts — appointments and new patient registrations — sourced from the existing `/dashboard/stats` endpoint.

**Architecture:** `HospitalStats` gains two zero-filled daily-count lists computed by one new grouped-count helper in `stats_service.py`, reused for both trends. The frontend adds two `recharts` cards to `Dashboard.jsx` in place of the old status card, styled like the existing charts in `Analytics.jsx`.

**Tech Stack:** FastAPI + SQLAlchemy 2.0 (async) + Pydantic v2 on the backend; React 18 + `recharts` (already a dependency, no install needed) on the frontend. Backend tests via pytest (`asyncio_mode = auto`).

## Global Constraints

- `appointments_trend`: 14 daily points (today inclusive), grouped from `Appointment.appointment_date`.
- `registrations_trend`: 30 daily points (today inclusive), grouped from `Patient.created_at`.
- Both lists are **zero-filled** — every day in the window appears exactly once, with `count: 0` for days with no activity. Never omit a day.
- No new endpoint, no new frontend fetch — both trends ride the existing `GET /dashboard/stats` response, already fetched once on dashboard mount.
- No date-range picker or other interactivity beyond hover tooltips.

---

### Task 1: Backend — trend data on `/dashboard/stats`

**Files:**
- Modify: `backend/app/schemas/dashboard.py`
- Modify: `backend/app/services/stats_service.py`
- Test: `backend/tests/unit/test_stats_service.py` (new)
- Test: `backend/tests/integration/test_clinical_workflows.py` (append)

**Interfaces:**
- Consumes: `Appointment.appointment_date` (`backend/app/models/appointment.py`, `Mapped[datetime]`), `Patient.created_at` (`backend/app/models/patient.py`, `Mapped[datetime]`) — both already exist.
- Produces: `TrendPoint(date: str, count: int)` and `HospitalStats.appointments_trend: list[TrendPoint]` / `HospitalStats.registrations_trend: list[TrendPoint]` — consumed by Task 2's frontend code as `stats.appointments_trend` / `stats.registrations_trend`, each item shaped `{date, count}`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/unit/test_stats_service.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && "./.venv/Scripts/python.exe" -m pytest tests/unit/test_stats_service.py -v`
Expected: FAIL — `AttributeError: 'HospitalStats' object has no attribute 'appointments_trend'` (the field doesn't exist yet).

- [ ] **Step 3: Add `TrendPoint` and the two new fields to the schema**

Replace `backend/app/schemas/dashboard.py` in full with:

```python
from pydantic import BaseModel


class TrendPoint(BaseModel):
    date: str
    count: int


class HospitalStats(BaseModel):
    total_patients: int
    dengue_cases_flagged: int
    available_doctors: int
    total_appointments: int
    total_lab_results: int
    low_stock_items: int
    open_alerts: int
    appointments_trend: list[TrendPoint]
    registrations_trend: list[TrendPoint]
```

- [ ] **Step 4: Add the trend-computing helper and wire it into `get_hospital_stats`**

Replace `backend/app/services/stats_service.py` in full with:

```python
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.lab_test import LabTest
from app.models.medical_record import MedicalRecord
from app.models.medicine import Medicine
from app.models.patient import Patient
from app.schemas.dashboard import HospitalStats, TrendPoint


async def _daily_trend(db: AsyncSession, date_column, days: int) -> list[TrendPoint]:
    """One TrendPoint per day for the last `days` days (today inclusive),
    zero-filled so every day appears even with no activity."""
    start = date.today() - timedelta(days=days - 1)
    day_expr = func.date(date_column)
    stmt = (
        select(day_expr.label("day"), func.count().label("cnt"))
        .where(date_column >= start)
        .group_by(day_expr)
    )
    result = await db.execute(stmt)
    counts = {row.day: row.cnt for row in result.all()}
    return [
        TrendPoint(
            date=(start + timedelta(days=i)).isoformat(),
            count=counts.get((start + timedelta(days=i)).isoformat(), 0),
        )
        for i in range(days)
    ]


async def get_hospital_stats(db: AsyncSession) -> HospitalStats:
    total_patients = await db.scalar(select(func.count()).select_from(Patient))
    dengue_cases_flagged = await db.scalar(
        select(func.count()).select_from(MedicalRecord).where(MedicalRecord.ml_dengue_predicted.is_(True))
    )
    total_doctors = await db.scalar(select(func.count()).select_from(Doctor))
    total_appointments = await db.scalar(select(func.count()).select_from(Appointment))
    total_lab_results = await db.scalar(select(func.count()).select_from(LabTest))

    medicines_result = await db.execute(select(Medicine).options(selectinload(Medicine.inventory)))
    low_stock_items = sum(
        1 for m in medicines_result.scalars().all() if m.inventory and m.inventory.is_low_stock
    )

    open_alerts = await db.scalar(select(func.count()).select_from(Alert).where(Alert.status == "open"))

    appointments_trend = await _daily_trend(db, Appointment.appointment_date, 14)
    registrations_trend = await _daily_trend(db, Patient.created_at, 30)

    return HospitalStats(
        total_patients=total_patients or 0,
        dengue_cases_flagged=dengue_cases_flagged or 0,
        available_doctors=total_doctors or 0,
        total_appointments=total_appointments or 0,
        total_lab_results=total_lab_results or 0,
        low_stock_items=low_stock_items,
        open_alerts=open_alerts or 0,
        appointments_trend=appointments_trend,
        registrations_trend=registrations_trend,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && "./.venv/Scripts/python.exe" -m pytest tests/unit/test_stats_service.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Add an integration test confirming the endpoint serializes the new fields**

Append to `backend/tests/integration/test_clinical_workflows.py`, right after the `# ── Pharmacy split ──` section's `test_pharmacy_create_and_low_stock_flag` (i.e. before `# ── RBAC sweep for new Nurse / Lab Technician endpoints ──`):

```python
# ── Dashboard stats ──────────────────────────────────────────────────────────────

async def test_dashboard_stats_includes_zero_filled_trends(client, world):
    resp = await client.get("/dashboard/stats", headers=world["admin"])
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["appointments_trend"]) == 14
    assert len(data["registrations_trend"]) == 30
    assert all("date" in p and "count" in p for p in data["appointments_trend"])
```

- [ ] **Step 7: Run the full backend suite**

Run: `cd backend && "./.venv/Scripts/python.exe" -m pytest -v`
Expected: all tests pass (baseline count + 3 new: 2 unit + 1 integration).

- [ ] **Step 8: Commit**

```bash
git add backend/app/schemas/dashboard.py backend/app/services/stats_service.py backend/tests/unit/test_stats_service.py backend/tests/integration/test_clinical_workflows.py
git commit -m "feat: add zero-filled appointments/registrations trend data to dashboard stats"
```

---

### Task 2: Frontend — replace System Status with trend charts

**Files:**
- Modify: `frontend/src/pages/admin/Dashboard.jsx`

**Interfaces:**
- Consumes: `stats.appointments_trend` / `stats.registrations_trend` (Task 1) — each an array of `{date: string, count: number}`, already present on the `stats` object this component fetches via `api.getHospitalStats()`.
- Produces: nothing consumed elsewhere — this is the leaf UI change.

- [ ] **Step 1: Add the recharts import**

At the top of `frontend/src/pages/admin/Dashboard.jsx`, change:

```jsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext.jsx";
```

to:

```jsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bar, BarChart, CartesianGrid, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import * as api from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext.jsx";
```

- [ ] **Step 2: Replace the System Status card with the two chart cards**

Replace this entire block (currently the `{/* ── System Status ── */}` comment through the `</div>` that closes the first card, right before the `<div className="card">` that starts "Hospital Highlights"):

```jsx
      {/* ── System Status ── */}
      <div className="grid-2">
        <div className="card">
          <div className="section-title">System Status</div>
          <table>
            <tbody>
              {[
                { label: "Database", status: "Operational", ok: true },
                { label: "ML Models", status: "Loaded", ok: true },
                { label: "API Server", status: "Running", ok: true },
                { label: "Pharmacy Alerts", status: stats?.low_stock_items > 0 ? `${stats.low_stock_items} items low` : "All stocked", ok: !stats?.low_stock_items },
                { label: "Dengue Alerts", status: stats?.open_alerts > 0 ? `${stats.open_alerts} open` : "Clear", ok: !stats?.open_alerts },
              ].map(({ label, status, ok }) => (
                <tr key={label}>
                  <td style={{ padding: "8px 0", color: "var(--color-text-muted)", width: 160 }}>{label}</td>
                  <td>
                    <span style={{
                      display: "inline-flex", alignItems: "center", gap: 6,
                      fontWeight: 600, fontSize: 13,
                      color: ok ? "#059669" : "#d97706",
                    }}>
                      <span style={{
                        width: 8, height: 8, borderRadius: "50%",
                        background: ok ? "#22c55e" : "#f59e0b",
                        display: "inline-block",
                        boxShadow: ok ? "0 0 0 2px #bbf7d0" : "0 0 0 2px #fde68a",
                      }} />
                      {status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="section-title">Hospital Highlights</div>
```

with:

```jsx
      {/* ── Activity Charts ── */}
      <div className="grid-2">
        <div className="card">
          <div className="section-title">Appointments — Last 14 Days</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={stats.appointments_trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={11} />
              <YAxis fontSize={11} allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="count" name="Appointments" stroke="#7c3aed" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="section-title">New Registrations — Last 30 Days</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.registrations_trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={11} />
              <YAxis fontSize={11} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="Registrations" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="section-title">Hospital Highlights</div>
```

(Everything after this point — the "Hospital Highlights" card's body and the closing tags — is unchanged; only the block above it is replaced. The `stats &&` guard a few lines up already ensures this whole section only renders once `stats` has loaded, so `stats.appointments_trend`/`stats.registrations_trend` are always defined here.)

- [ ] **Step 3: Manually verify in the browser**

This app has no JS test framework — verify by running the app:

1. Start the backend: `cd backend && uvicorn app.main:app --reload` (`http://127.0.0.1:8000`).
2. Start the frontend: `cd frontend && npm run dev` (`http://127.0.0.1:5173`).
3. Log in as an admin (see `backend/seed.py`'s Admin section, or any seeded admin account) or a doctor (dashboard stats are readable by both roles per `backend/app/routers/dashboard.py`).
4. Open the dashboard: confirm the old "System Status" card (with "Database: Operational" etc.) is gone.
5. Confirm two new cards render: "Appointments — Last 14 Days" (a line chart) and "New Registrations — Last 30 Days" (a bar chart), each with a visible X-axis of dates and a working hover tooltip.
6. Confirm "Hospital Highlights" still renders below/beside them as before.
7. If the seeded dev DB has little recent activity, most points will show near zero — that's expected and correct (zero-fill working as designed), not a bug.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/admin/Dashboard.jsx
git commit -m "feat: replace System Status card with appointments/registrations trend charts"
```

---

## Post-plan check

After both tasks: run `cd backend && "./.venv/Scripts/python.exe" -m pytest -v` one final time and confirm the manual browser walkthrough in Task 2 Step 3 was completed.
