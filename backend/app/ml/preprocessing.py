"""CSV loading + feature engineering for the two datasets:
- dengue_dataset_withclimate.csv   -> regression (predict Dengue_Cases)
- dengue_dataset_withsymptoms.csv  -> classification (predict Outcome)
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).parent / "data"
CLIMATE_CSV = DATA_DIR / "dengue_dataset_withclimate.csv"
SYMPTOMS_CSV = DATA_DIR / "dengue_dataset_withsymptoms.csv"

CLIMATE_FEATURE_COLUMNS = [
    "Month",
    "Latitude",
    "Longitude",
    "Population_Density",
    "Precipitation_mm",
    "Surface_Pressure_kPa",
    "Specific_Humidity_g_per_kg",
    "Relative_Humidity_pct",
    "Avg_Temperature_C",
    "Max_Temperature_C",
    "Min_Temperature_C",
    "Temperature_Range_C",
    "Wind_Speed_10m_m_s",
    "Wind_Speed_50m_m_s",
]
CLIMATE_TARGET_COLUMN = "Dengue_Cases"

# Classic dengue symptoms + WHO warning signs (abdominal pain/tenderness,
# persistent vomiting, mucosal bleeding, lethargy/restlessness, liver
# enlargement) + comorbidities + rapid serology markers (NS1/IgG/IgM) — all
# present as 0/1 columns in dengue_dataset_withsymptoms.csv.
SYMPTOM_BINARY_COLUMNS = [
    "Headache", "Retro_Orbital_Pain", "Myalgia", "Rash",
    "Persistent_vomiting", "Abdominal_pain", "Bleeding", "Restlessness", "Lethargy", "Liver_enlargement",
    "Previous_dengue_history", "Diabetes", "Hypertension", "Obesity", "Pregnancy",
    "NS1", "IgG", "IgM",
]
WHO_WARNING_SIGN_COLUMNS = [
    "Persistent_vomiting", "Abdominal_pain", "Bleeding", "Restlessness", "Lethargy", "Liver_enlargement",
]
# Platelet/Hematocrit day1+day3+change_rate are precomputed lab-trend
# features already present in the dataset (a falling platelet count with a
# rising hematocrit is the classic plasma-leakage warning sign).
SYMPTOM_NUMERIC_COLUMNS = [
    "Age", "Days_since_fever_onset", "Body_Temperature",
    "Platelet_day1", "Platelet_day3", "Platelet_change_rate",
    "Hematocrit_day1", "Hematocrit_day3", "Hematocrit_change_rate",
    "WBC_Count",
]
SYMPTOM_TARGET_COLUMN = "Outcome"

JOINT_PAIN_MAP = {"No_Joint_Pain": 0, "Moderate": 1, "Severe": 2}
GENDER_MAP = {"Male": 0, "Female": 1}
# Ordinal calendar position rather than an alphabetically-sorted label code —
# months are cyclical/ordered, and a tree model can exploit "later in the
# monsoon season" as a real signal if the encoding preserves that order.
MONTH_ORDER = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}


class LabelEncoder:

    def __init__(self):
        self.classes_: list[str] = []
        self._index: dict[str, int] = {}

    def fit(self, values) -> "LabelEncoder":
        self.classes_ = sorted(set(values))
        self._index = {v: i for i, v in enumerate(self.classes_)}
        return self

    def transform(self, values) -> list[int]:
        # Unseen categories fall back to a stable hashed bucket instead of raising.
        return [self._index.get(v, len(self.classes_)) for v in values]

    def fit_transform(self, values) -> list[int]:
        self.fit(values)
        return self.transform(values)


def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_climate_features(rows: list[dict] | None = None):
    """Returns (X, y, feature_names, district_encoder, raw_rows)."""
    rows = rows if rows is not None else load_csv(CLIMATE_CSV)

    district_encoder = LabelEncoder()
    district_codes = district_encoder.fit_transform([r["District"] for r in rows])

    X = []
    y = []
    for row, district_code in zip(rows, district_codes):
        try:
            features = [float(row[col]) for col in CLIMATE_FEATURE_COLUMNS]
        except (ValueError, KeyError):
            continue
        features.append(float(district_code))
        X.append(features)
        y.append(float(row[CLIMATE_TARGET_COLUMN]))

    feature_names = CLIMATE_FEATURE_COLUMNS + ["District_Code"]
    return np.array(X, dtype=float), np.array(y, dtype=float), feature_names, district_encoder, rows


def build_symptom_features(rows: list[dict] | None = None):
    """Returns (X, y, feature_names, district_encoder, raw_rows)."""
    rows = rows if rows is not None else load_csv(SYMPTOMS_CSV)

    district_encoder = LabelEncoder()
    district_codes = district_encoder.fit_transform([r["District"] for r in rows])

    X = []
    y = []
    for row, district_code in zip(rows, district_codes):
        try:
            gender = GENDER_MAP.get(row["Gender"], 0)
            numeric = [float(row[col]) for col in SYMPTOM_NUMERIC_COLUMNS]
            binary = [float(row[col]) for col in SYMPTOM_BINARY_COLUMNS]
            joint_pain = JOINT_PAIN_MAP.get(row["Joint_Pain"], 0)
            month = MONTH_ORDER.get(row["Visit_Month"], 0)
        except (ValueError, KeyError):
            continue
        features = [float(gender)] + numeric + [float(joint_pain), float(month), float(district_code)] + binary
        X.append(features)
        y.append(float(row[SYMPTOM_TARGET_COLUMN]))

    feature_names = (
        ["Gender"] + SYMPTOM_NUMERIC_COLUMNS + ["Joint_Pain", "Visit_Month", "District_Code"] + SYMPTOM_BINARY_COLUMNS
    )
    return np.array(X, dtype=float), np.array(y, dtype=int), feature_names, district_encoder, rows


def encode_single_patient(payload: dict, district_encoder: "LabelEncoder") -> np.ndarray:
    """Builds one feature row (same order as build_symptom_features) from a
    PatientDiagnosisRequest-shaped dict for live prediction. `district_encoder`
    must be the encoder fitted during training (persisted in the model
    artifact) so codes stay consistent between train and inference."""
    gender = GENDER_MAP.get(payload["gender"], 0)
    platelet_change_rate = payload["platelet_day3"] - payload["platelet_day1"]
    hematocrit_change_rate = payload["hematocrit_day3"] - payload["hematocrit_day1"]
    numeric = [
        float(payload["age"]),
        float(payload["days_since_fever_onset"]),
        float(payload["body_temperature"]),
        float(payload["platelet_day1"]),
        float(payload["platelet_day3"]),
        float(platelet_change_rate),
        float(payload["hematocrit_day1"]),
        float(payload["hematocrit_day3"]),
        float(hematocrit_change_rate),
        float(payload["wbc_count"]),
    ]
    joint_pain = JOINT_PAIN_MAP.get(payload["joint_pain"], 0)
    month = MONTH_ORDER.get(payload.get("visit_month"), 0)
    district_code = district_encoder.transform([payload.get("district", "")])[0]
    binary = [float(payload[col.lower()]) for col in SYMPTOM_BINARY_COLUMNS]
    row = [float(gender)] + numeric + [float(joint_pain), float(month), float(district_code)] + binary
    return np.array([row], dtype=float)
