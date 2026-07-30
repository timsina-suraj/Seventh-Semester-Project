# MediShield — Intelligent Hospital Management System

A hospital management system for Nepal with an integrated dengue-outbreak
prediction and patient-diagnosis AI layer, built against an 18-module spec
covering auth/security, the full clinical workflow, and analytics.

- **Backend**: FastAPI (fully async) + SQLAlchemy 2.0 async ORM + Alembic migrations (SQLite for local dev, MySQL-ready via one env var)
- **Architecture**: Repository pattern + service layer + FastAPI `Depends()` dependency injection, domain exceptions translated to HTTP by a single handler, structured logging
- **Security**: JWT auth, OTP-based first login / password reset, role-based access control across 6 roles, bcrypt password hashing, AES-256-GCM field-level encryption for sensitive patient data, audit + login logs
- **ML**: Decision Tree / Random Forest / Gradient-Boosted ("XGBoost-style") regressors + classifiers, implemented **from scratch** on numpy — no scikit-learn/xgboost — trained on the two datasets in `backend/app/ml/data/`
- **Frontend**: React + Vite, role-aware dashboards and navigation, Recharts model-metric charts, a Leaflet-based Nepal district risk map
- **Tests**: pytest + pytest-asyncio + httpx, unit + integration coverage against an in-memory SQLite DB

## Roles

Admin, Doctor, Nurse, Receptionist, Lab Technician, Patient — each with its
own login, dashboard, and navigation. Admin creates all staff accounts;
Receptionist registers patients; the very first Admin account is created
once via a bootstrap script (see below), not through the UI.

## Quick start

**Backend** (from `backend/`):

```bash
python -m venv .venv
.venv\Scripts\activate            # .venv/bin/activate on Linux/Mac
pip install -r requirements.txt

copy .env.example .env            # cp on Linux/Mac — then fill in JWT_SECRET_KEY / ENCRYPTION_KEY
alembic upgrade head              # creates the schema (MediShield_db.db for SQLite)

python -m scripts.bootstrap_admin --email admin@example.com --name "System Administrator"
# — or, for a fully-populated demo dataset instead of one bare admin account:
python seed.py                    # creates ~35 users across all 6 roles + realistic sample data

python -m app.ml.train_dengue_prediction  # trains + persists the district-outbreak regressors
python -m app.ml.train_diagnosis          # trains + persists the patient-diagnosis classifiers

uvicorn app.main:app --reload     # http://127.0.0.1:8000  (interactive docs at /docs)
```

Email delivery (registration/OTP/notification emails) needs an SMTP server;
for local dev point `SMTP_HOST`/`SMTP_PORT` in `.env` at
[Mailpit](https://github.com/axllent/mailpit) (`./mailpit/mailpit.exe`, web
UI at http://localhost:8025) or any local SMTP catcher.

```mailpit.exe --database mailpitdata\mailpit.db``` with database that stores previous mails

**Frontend** (from `frontend/`, in a second terminal):

```bash
npm install
npm run dev                       # http://127.0.0.1:5173, proxies /api -> :8000
```

If you ran `seed.py`, sign in with any of the seeded accounts (all
`is_active=true`, no OTP needed for the demo):

| Role            | Email                     | Password       |
|-----------------|---------------------------|----------------|
| Admin           | admin@example.com         | Admin@12345    |
| Doctor          | anjali@example.com        | Doctor@1234    |
| Nurse           | nurse1@example.com        | Nurse@1234     |
| Receptionist    | recept1@example.com       | Recept@1234    |
| Lab Technician  | labtech1@example.com      | LabTech@1234   |
| Patient         | patient01@example.com     | Patient@1234   |

A real account created through the app (not seeded) starts inactive with no
password and goes through the first-login OTP flow instead.

## What's implemented

**Auth & security** — normalized per-role tables (`users` + one profile
table per role), OTP-gated first login and password reset (with expiry,
attempt limits, and a resend cooldown), forced password change, an
admin-initiated password reset that re-triggers the OTP flow, audit logs,
and login logs.

**Clinical workflow** — patient records (AES-256-GCM encrypted phone/
address/emergency contact), doctor-managed weekly availability with
real slot-conflict validation on booking, the full appointment lifecycle
(Pending → Confirmed/Completed/Cancelled/No-show), EMR entries linked to
appointments, structured medical history / chronic conditions, prescriptions
with line items, a lab test request → result workflow, and pharmacy
inventory with low-stock tracking.

**Documents & exports** — per-patient file uploads (any type, size-limited,
randomly-named on disk) with role-scoped access and an inline preview for
images/PDFs; PDF exports for medical records, prescriptions, and lab
reports via ReportLab.

**Notifications** — background (non-blocking) emails for account creation,
first-login/password-reset OTPs, appointment booked/status-changed, lab
result ready, and prescription issued.

**Search & filtering** — name/ID search on patients, doctors, and
pharmacy items; department/specialization filters on doctors; status and
date-range filters on appointments.

**AI / ML** — dengue outbreak forecasting per district (regression) and
dengue-positive diagnosis prediction per patient (classification,
including WHO warning signs, comorbidities, rapid serology, and lab-trend
features), both comparing 3 from-scratch model families with
MAE/RMSE/R² and Accuracy/Precision/Recall/F1. Positive predictions and
high-risk districts raise alerts automatically. An AI Analytics dashboard
(train + compare models), a Nepal district risk map, and an Alerts inbox
round it out. A dataset-quality pass (missing values, duplicates, outliers)
runs before every training run.

## What's simplified for this scaffold

- The Nepal risk map renders colored markers (from each district's
  lat/long) rather than filled district polygons — offline district
  boundary GeoJSON wasn't available.
- District case forecasts are single-step "next month" predictions from
  each district's most recent known climate reading, not a full
  time-series model.
- Prescriptions record medicine names as free text (matching the spec's own
  table shape) rather than linking to the pharmacy's `medicines` table, so
  issuing one doesn't automatically decrement inventory.
- Uploaded documents are stored on local disk (`backend/uploads/`), not
  object storage — fine for a single-instance deployment, not for a
  multi-node one.

## Tests

```bash
cd backend && pytest
```
