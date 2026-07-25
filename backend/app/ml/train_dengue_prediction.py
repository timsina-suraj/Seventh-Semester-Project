"""Trains and compares the 3 from-scratch regressors (Decision Tree, Random
Forest, Gradient-Boosted 'XGBoost') on dengue_dataset_withclimate.csv to
predict Dengue_Cases, then persists the best model + supporting artifacts.

Run directly:  python -m app.ml.train_dengue_prediction
Or imported and called from the /ml/train/dengue API endpoint.
"""
from __future__ import annotations

import numpy as np

from app.ml import model_store
from app.ml.decision_tree import DecisionTreeRegressor
from app.ml.gradient_boosting import GBRegressor
from app.ml.metrics import regression_report, train_test_split
from app.ml.preprocessing import CLIMATE_FEATURE_COLUMNS, build_climate_features, load_csv, CLIMATE_CSV
from app.ml.random_forest import RandomForestRegressor
from app.validation.validators import validate_dataset

MODEL_KEY = "dengue_regressors"


def _latest_row_per_district(rows: list[dict]) -> dict:
    """Keeps the most recent (highest Year, Month) row per district, used as
    the feature basis for 'next period' forecasting."""
    latest: dict[str, dict] = {}
    for row in rows:
        district = row["District"]
        key = (int(row["Year"]), int(row["Month"]))
        if district not in latest or key > latest[district]["_key"]:
            entry = dict(row)
            entry["_key"] = key
            latest[district] = entry
    return latest


def train_and_store() -> dict:
    rows = load_csv(CLIMATE_CSV)

    quality = validate_dataset(
        rows,
        required_columns=CLIMATE_FEATURE_COLUMNS + ["Dengue_Cases", "District"],
        numeric_outlier_columns=["Dengue_Cases", "Precipitation_mm"],
    )

    X, y, feature_names, district_encoder, _ = build_climate_features(rows)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        # Deeper trees and smaller leaves let the regressors capture more signal.
        "decision_tree": DecisionTreeRegressor(max_depth=10, min_samples_split=2),
        "random_forest": RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=2),
        "xgboost": GBRegressor(n_estimators=150, learning_rate=0.1, max_depth=4, min_samples_split=2),
    }

    metrics = {}
    fitted = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        preds = np.clip(preds, 0, None) 
        metrics[name] = regression_report(y_test, preds)
        fitted[name] = model

    # Best = lowest RMSE
    best_model_name = min(metrics, key=lambda k: metrics[k]["rmse"])

    # Aggregate Actual vs Predicted over the test set
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_idx = feature_names.index("Month")
    monthly_stats = {m: {"Actual": 0.0, "Predicted": 0.0, "Count": 0} for m in range(1, 13)}
    
    best_preds = fitted[best_model_name].predict(X_test)
    best_preds = np.clip(best_preds, 0, None)
    
    for i in range(len(y_test)):
        m = int(X_test[i, month_idx])
        monthly_stats[m]["Actual"] += y_test[i]
        monthly_stats[m]["Predicted"] += best_preds[i]
        monthly_stats[m]["Count"] += 1
        
    actual_vs_predicted = []
    for m in range(1, 13):
        if monthly_stats[m]["Count"] > 0:
            actual_vs_predicted.append({
                "month": month_names[m - 1],
                "Actual": round(monthly_stats[m]["Actual"] / monthly_stats[m]["Count"], 1),
                "Predicted": round(monthly_stats[m]["Predicted"] / monthly_stats[m]["Count"], 1)
            })
        else:
            actual_vs_predicted.append({"month": month_names[m - 1], "Actual": 0, "Predicted": 0})

    # Aggregate Weather Data over the whole dataset
    monthly_weather = {m: {"Cases": 0.0, "Rainfall": 0.0, "Temp": 0.0, "Count": 0} for m in range(1, 13)}
    for row in rows:
        try:
            m = int(row["Month"])
            monthly_weather[m]["Cases"] += float(row["Dengue_Cases"])
            monthly_weather[m]["Rainfall"] += float(row["Precipitation_mm"])
            monthly_weather[m]["Temp"] += float(row["Avg_Temperature_C"])
            monthly_weather[m]["Count"] += 1
        except (ValueError, KeyError):
            continue
            
    weather_data = []
    for m in range(1, 13):
        if monthly_weather[m]["Count"] > 0:
            weather_data.append({
                "month": month_names[m - 1],
                "Cases": round(monthly_weather[m]["Cases"] / monthly_weather[m]["Count"], 1),
                "Rainfall": round(monthly_weather[m]["Rainfall"] / monthly_weather[m]["Count"], 1),
                "Temp": round(monthly_weather[m]["Temp"] / monthly_weather[m]["Count"], 1)
            })
        else:
            weather_data.append({"month": month_names[m - 1], "Cases": 0, "Rainfall": 0, "Temp": 0})

    artifact = {
        "models": fitted,
        "best_model_name": best_model_name,
        "feature_names": feature_names,
        "district_encoder": district_encoder,
        "metrics": metrics,
        "latest_by_district": _latest_row_per_district(rows),
        "actual_vs_predicted": actual_vs_predicted,
        "weather_data": weather_data,
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
        print(f"{name:15s}  MAE={m['mae']:.2f}  RMSE={m['rmse']:.2f}  R2={m['r2']:.3f}")
    print("Best model:", result["best_model_name"])
