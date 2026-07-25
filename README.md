# MediShield Intelligent Hospital Management System

A hospital management system for Nepal with an integrated dengue-outbreak
prediction and patient-diagnosis AI layer, built per the project spec:

- **Backend**: FastAPI + SQLAlchemy (SQLite for local dev, MySQL-ready via one env var)
- **Security**: JWT auth, role-based access control, bcrypt password hashing, AES-256-GCM field encryption for sensitive patient data
- **ML**: Decision Tree / Random Forest / Gradient-Boosted ("XGBoost-style") regressors + classifiers, implemented **from scratch** on numpy — no scikit-learn/xgboost — trained on the two real datasets in `backend/app/ml/data/`
- **Frontend**: React + Vite, role-aware dashboards, Recharts model-metric charts, a Leaflet-based Nepal district risk map

## Quick start

**Backend** (from `backend/`):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py                          # creates hmms.db + admin user + sample data
python -m app.ml.train_dengue_prediction # trains + persists the regression models
python -m app.ml.train_diagnosis         # trains + persists the classification models
uvicorn app.main:app --reload            # http://127.0.0.1:8000  (docs at /docs)
```

**Frontend** (from `frontend/`, in a second terminal):

```bash
npm install
npm run dev                              # http://127.0.0.1:5173, proxies /api -> :8000
```

Log in with the seeded admin: `admin` / `Admin@12345`.

See `backend/README.md` for details on switching to MySQL and the ML pipeline.

## What's implemented

- Full CRUD for patients, doctors, appointments, lab results, pharmacy inventory, and encrypted medical records, gated by role (Administrator / Doctor / Receptionist / Patient).
- Dengue outbreak forecasting per district (regression) and dengue-positive diagnosis prediction per patient (classification), both comparing 3 from-scratch model families with MAE/RMSE/R² and Accuracy/Precision/Recall/F1.
- Automatic High/Very-High district risk alerts and dengue-positive patient alerts.
- An AI Analytics dashboard (train + compare models), a Nepal district risk map, and an Alerts inbox.
- Dataset-quality validation (missing values, duplicates, outliers) run before every training pass.

## What's simplified for this scaffold

- The "Nepal risk map" renders colored markers (using each district's lat/long from the dataset) rather than filled district polygons, since offline district boundary GeoJSON wasn't available.
- District case forecasts are single-step "next month" predictions built from each district's most recent known climate reading, not a full time-series model.
- No database migrations tool (Alembic) — tables are created via `Base.metadata.create_all()`. Add Alembic before this goes to production against a persistent MySQL database.
