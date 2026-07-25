"""Trains and compares the 3 from-scratch classifiers (Decision Tree, Random
Forest, Gradient-Boosted 'XGBoost') on dengue_dataset_withsymptoms.csv to
predict Outcome (dengue positive/negative), then persists the best model.

Run directly:  python -m app.ml.train_diagnosis
Or imported and called from the /ml/train/diagnosis API endpoint.
"""
from __future__ import annotations

from app.ml import model_store
from app.ml.decision_tree import DecisionTreeClassifier
from app.ml.gradient_boosting import GBClassifier
from app.ml.metrics import classification_report, train_test_split
from app.ml.preprocessing import (
    SYMPTOM_BINARY_COLUMNS,
    SYMPTOM_NUMERIC_COLUMNS,
    build_symptom_features,
    load_csv,
    SYMPTOMS_CSV,
)
from app.ml.random_forest import RandomForestClassifier
from app.validation.validators import validate_dataset

MODEL_KEY = "diagnosis_classifiers"


def train_and_store() -> dict:
    rows = load_csv(SYMPTOMS_CSV)

    quality = validate_dataset(
        rows,
        required_columns=SYMPTOM_NUMERIC_COLUMNS + SYMPTOM_BINARY_COLUMNS + ["Outcome", "Gender", "Joint_Pain"],
        numeric_outlier_columns=["Platelet_Count", "WBC_Count", "Body_Temperature"],
    )

    X, y, feature_names, _ = build_symptom_features(rows)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        # Shallower trees with larger leaves reduce classifier variance.
        "decision_tree": DecisionTreeClassifier(max_depth=4, min_samples_split=12, n_classes=2),
        "random_forest": RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_split=12, n_classes=2),
        "xgboost": GBClassifier(n_estimators=100, learning_rate=0.05, max_depth=2, min_samples_split=12),
    }

    metrics = {}
    fitted = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        metrics[name] = classification_report(y_test, preds)
        fitted[name] = model

    # Best = highest F1 (balances precision/recall, important for a clinical positive class)
    best_model_name = max(metrics, key=lambda k: metrics[k]["f1"])

    pos_count = sum(1 for row in rows if int(row.get("Outcome", 0)) == 1)
    neg_count = len(rows) - pos_count
    diagnosis_dist = [
        {"name": "Dengue Positive", "value": pos_count},
        {"name": "Dengue Negative", "value": neg_count}
    ]

    target_symptoms = ["Joint_Pain", "Headache", "Retro_Orbital_Pain", "Myalgia", "Rash"]
    symptoms_data = []
    for col in target_symptoms:
        if col == "Joint_Pain":
            count = sum(1 for row in rows if row.get("Joint_Pain", "None") != "None")
        else:
            count = sum(1 for row in rows if int(row.get(col, 0)) == 1)
        symptoms_data.append({"symptom": col.replace("_", " "), "count": count})
    
    symptoms_data.sort(key=lambda x: x["count"], reverse=True)

    artifact = {
        "models": fitted,
        "best_model_name": best_model_name,
        "feature_names": feature_names,
        "metrics": metrics,
        "diagnosis_dist": diagnosis_dist,
        "symptoms_data": symptoms_data,
        "dataset_quality": quality.as_dict(),
        "rows_trained_on": len(rows),
    }
    model_store.save(MODEL_KEY, artifact)
    return artifact


def load_artifact() -> dict | None:
    return model_store.load(MODEL_KEY)


if __name__ == "__main__":
    result = train_and_store()
    print("Dataset quality:", result["dataset_quality"])
    print("Rows trained on:", result["rows_trained_on"])
    for name, m in result["metrics"].items():
        print(f"{name:15s}  Acc={m['accuracy']:.3f}  Prec={m['precision']:.3f}  Rec={m['recall']:.3f}  F1={m['f1']:.3f}")
    print("Best model:", result["best_model_name"])
