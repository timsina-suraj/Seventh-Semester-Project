"""Phase D regression test: the symptoms CSV schema was replaced (WHO
warning signs, comorbidities, serology, lab-trend columns) but the
preprocessing pipeline was left pointing at the old column names — every row
silently failed to parse and the model trained on ~0 rows. This test guards
against that ever happening again silently: with the real CSV wired up,
essentially all 10k rows must parse."""
from app.ml.preprocessing import (
    SYMPTOM_BINARY_COLUMNS,
    SYMPTOM_NUMERIC_COLUMNS,
    build_symptom_features,
    encode_single_patient,
    load_csv,
    SYMPTOMS_CSV,
)


def test_build_symptom_features_parses_almost_every_row():
    rows = load_csv(SYMPTOMS_CSV)
    X, y, feature_names, district_encoder, _ = build_symptom_features(rows)

    assert len(X) > len(rows) * 0.95  # a handful of malformed rows is fine, silently dropping ~all is not
    assert X.shape[1] == len(feature_names)
    assert set(y.tolist()) <= {0, 1}
    assert len(district_encoder.classes_) > 1


def test_feature_row_length_matches_feature_names():
    _, _, feature_names, district_encoder, _ = build_symptom_features()
    expected_len = 1 + len(SYMPTOM_NUMERIC_COLUMNS) + 3 + len(SYMPTOM_BINARY_COLUMNS)  # +Gender +JointPain/Month/District

    assert len(feature_names) == expected_len

    payload = {
        "gender": "Female", "age": 30, "district": district_encoder.classes_[0], "visit_month": "August",
        "days_since_fever_onset": 2, "body_temperature": 39.0,
        "platelet_day1": 300000, "platelet_day3": 150000,
        "hematocrit_day1": 42.0, "hematocrit_day3": 45.0, "wbc_count": 5000,
        "joint_pain": "Severe", "headache": True, "retro_orbital_pain": False, "myalgia": True, "rash": False,
        "persistent_vomiting": False, "abdominal_pain": False, "bleeding": False,
        "restlessness": False, "lethargy": False, "liver_enlargement": False,
        "previous_dengue_history": False, "diabetes": False, "hypertension": False,
        "obesity": False, "pregnancy": False, "ns1": True, "igg": False, "igm": False,
    }
    row = encode_single_patient(payload, district_encoder)

    assert row.shape == (1, expected_len)


def test_encode_single_patient_computes_change_rate_like_the_dataset():
    _, _, feature_names, district_encoder, _ = build_symptom_features()
    payload = {
        "gender": "Male", "age": 40, "district": "", "visit_month": "",
        "days_since_fever_onset": 3, "body_temperature": 38.5,
        "platelet_day1": 300000, "platelet_day3": 200000,
        "hematocrit_day1": 40.0, "hematocrit_day3": 44.0, "wbc_count": 6000,
        "joint_pain": "No_Joint_Pain", "headache": False, "retro_orbital_pain": False, "myalgia": False, "rash": False,
        "persistent_vomiting": False, "abdominal_pain": False, "bleeding": False,
        "restlessness": False, "lethargy": False, "liver_enlargement": False,
        "previous_dengue_history": False, "diabetes": False, "hypertension": False,
        "obesity": False, "pregnancy": False, "ns1": False, "igg": False, "igm": False,
    }
    row = encode_single_patient(payload, district_encoder)
    platelet_change_idx = feature_names.index("Platelet_change_rate")
    hematocrit_change_idx = feature_names.index("Hematocrit_change_rate")

    assert row[0, platelet_change_idx] == -100000  # 200000 - 300000
    assert row[0, hematocrit_change_idx] == 4.0  # 44.0 - 40.0


def test_unseen_district_falls_back_instead_of_raising():
    _, _, _, district_encoder, _ = build_symptom_features()
    payload = {
        "gender": "Male", "age": 40, "district": "Atlantis", "visit_month": "",
        "days_since_fever_onset": 3, "body_temperature": 38.5,
        "platelet_day1": 300000, "platelet_day3": 300000,
        "hematocrit_day1": 40.0, "hematocrit_day3": 40.0, "wbc_count": 6000,
        "joint_pain": "No_Joint_Pain", "headache": False, "retro_orbital_pain": False, "myalgia": False, "rash": False,
        "persistent_vomiting": False, "abdominal_pain": False, "bleeding": False,
        "restlessness": False, "lethargy": False, "liver_enlargement": False,
        "previous_dengue_history": False, "diabetes": False, "hypertension": False,
        "obesity": False, "pregnancy": False, "ns1": False, "igg": False, "igm": False,
    }
    row = encode_single_patient(payload, district_encoder)  # should not raise
    assert row is not None
