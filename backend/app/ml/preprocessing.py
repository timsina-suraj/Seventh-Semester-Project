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

SYMPTOM_BINARY_COLUMNS = ["Headache", "Retro_Orbital_Pain", "Myalgia", "Rash"]
SYMPTOM_NUMERIC_COLUMNS = ["Age", "Fever_Duration", "Body_Temperature", "Platelet_Count", "WBC_Count"]
SYMPTOM_TARGET_COLUMN = "Outcome"

JOINT_PAIN_MAP = {"None": 0, "Moderate": 1, "Severe": 2}
GENDER_MAP = {"Male": 0, "Female": 1}


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
    """Returns (X, y, feature_names, raw_rows)."""
    rows = rows if rows is not None else load_csv(SYMPTOMS_CSV)

    X = []
    y = []
    for row in rows:
        try:
            gender = GENDER_MAP.get(row["Gender"], 0)
            numeric = [float(row[col]) for col in SYMPTOM_NUMERIC_COLUMNS]
            binary = [float(row[col]) for col in SYMPTOM_BINARY_COLUMNS]
            joint_pain = JOINT_PAIN_MAP.get(row["Joint_Pain"], 0)
        except (ValueError, KeyError):
            continue
        features = [float(gender)] + numeric + [float(joint_pain)] + binary
        X.append(features)
        y.append(float(row[SYMPTOM_TARGET_COLUMN]))

    feature_names = ["Gender"] + SYMPTOM_NUMERIC_COLUMNS + ["Joint_Pain"] + SYMPTOM_BINARY_COLUMNS
    return np.array(X, dtype=float), np.array(y, dtype=int), feature_names, rows


def encode_single_patient(payload: dict) -> np.ndarray:
    """Builds one feature row (same order as build_symptom_features) from a
    PatientDiagnosisRequest-shaped dict for live prediction."""
    gender = GENDER_MAP.get(payload["gender"], 0)
    numeric = [
        float(payload["age"]),
        float(payload["fever_duration"]),
        float(payload["body_temperature"]),
        float(payload["platelet_count"]),
        float(payload["wbc_count"]),
    ]
    joint_pain = JOINT_PAIN_MAP.get(payload["joint_pain"], 0)
    binary = [
        float(payload["headache"]),
        float(payload["retro_orbital_pain"]),
        float(payload["myalgia"]),
        float(payload["rash"]),
    ]
    row = [float(gender)] + numeric + [float(joint_pain)] + binary
    return np.array([row], dtype=float)
