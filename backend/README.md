# MediShield Backend (FastAPI)

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    

pip install -r requirements.txt
python seed.py                # creates .db (SQLite) + admin user + sample data
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

Seeded admin login: `username=admin`, `password=Admin@12345` (change this immediately in a real deployment).

## Switching to MySQL

No code changes required — just point `DATABASE_URL` at MySQL, e.g. in a `.env`
file (see `.env.example`):

```
DATABASE_URL=mysql+pymysql://hmms_user:password@localhost:3306/hmms
```

Then re-run `python seed.py` to create tables + seed data against MySQL.

## Training the ML models

The two datasets already live in `app/ml/data/`. Train both model families
directly from the CLI (prints metrics + persists to `app/ml/model_store/`):

```bash
python -m app.ml.train_dengue_prediction
python -m app.ml.train_diagnosis
```

Or trigger training via the API (as an admin): `POST /ml/train/dengue` and
`POST /ml/train/diagnosis`. Prediction endpoints
(`GET /ml/predict/district/{district}`, `GET /ml/risk-map`,
`POST /ml/predict/patient`) will 400 until each model has been trained once.

## Project layout

```
app/
  main.py            FastAPI app + router registration
  config.py           Settings (env-driven)
  database.py          SQLAlchemy engine/session
  security/            JWT auth, RBAC, AES-256-GCM field encryption
  models/               SQLAlchemy ORM models
  schemas/              Pydantic request/response models
  routers/               API endpoints
  services/               Business logic (alerts, risk classification, stats)
  validation/              Input + dataset quality validators
  ml/                       From-scratch ML (no scikit-learn/xgboost)
    tree_core.py            Shared CART engine
    decision_tree.py         Decision Tree Regressor/Classifier
    random_forest.py          Random Forest Regressor/Classifier
    gradient_boosting.py       Gradient-boosted ("XGBoost-style") Regressor/Classifier
    train_dengue_prediction.py  Trains regressors on the climate dataset
    train_diagnosis.py           Trains classifiers on the symptoms dataset
    data/                          The two CSV datasets
    model_store/                    Pickled trained artifacts
```
