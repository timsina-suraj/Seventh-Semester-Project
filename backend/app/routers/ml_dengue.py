import requests
from datetime import datetime
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml import train_dengue_prediction
from app.ml.preprocessing import CLIMATE_FEATURE_COLUMNS, CLIMATE_TARGET_COLUMN
from app.schemas.ml import DistrictRiskPoint, RegressionMetrics, TrainDengueResponse
from app.security.rbac import require_role
from app.services.alert_service import create_district_alert
from app.services.risk_classifier import classify_risk

router = APIRouter(prefix="/ml", tags=["ml-dengue"])


def _get_artifact():
    artifact = train_dengue_prediction.load_artifact()
    if artifact is None:
        raise HTTPException(
            status_code=400,
            detail="Dengue prediction model has not been trained yet. Call POST /ml/train/dengue first.",
        )
    return artifact


import time

_WEATHER_CACHE = {}
_CACHE_TTL = 3600  # 1 hour in seconds

def _fetch_live_weather_bulk(lat_lon_pairs):
    if not lat_lon_pairs:
        return {}
    
    current_time = time.time()
    results = {}
    missing_pairs = []

    for pair in lat_lon_pairs:
        cached = _WEATHER_CACHE.get(pair)
        if cached and (current_time - cached["timestamp"] < _CACHE_TTL):
            results[pair] = cached["data"]
        else:
            missing_pairs.append(pair)

    if not missing_pairs:
        return results

    lats = ",".join(str(lat) for lat, _ in missing_pairs)
    lons = ",".join(str(lon) for _, lon in missing_pairs)
    
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&current=temperature_2m,relative_humidity_2m,precipitation,surface_pressure,wind_speed_10m"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Weather API failed: {e}")
        return results

    # data could be a list if multiple, or a dict if single
    if isinstance(data, dict) and "current" in data:
        data = [data]

    for i, pair in enumerate(missing_pairs):
        try:
            current = data[i].get("current", {})
            weather_data = {
                "temperature": current.get("temperature_2m"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation"),
                "pressure": current.get("surface_pressure"),
                "wind": current.get("wind_speed_10m"),
            }
            results[pair] = weather_data
            _WEATHER_CACHE[pair] = {"data": weather_data, "timestamp": current_time}
        except IndexError:
            pass
            
    return results


def _build_feature_row(artifact: dict, district: str, live_weather: dict = None):
    latest = artifact["latest_by_district"].get(district)
    if latest is None:
        raise HTTPException(status_code=404, detail=f"No climate data on file for district '{district}'")

    features = [float(latest[col]) for col in CLIMATE_FEATURE_COLUMNS]
    
    # Overwrite features with live weather if available
    if live_weather:
        temp_idx = CLIMATE_FEATURE_COLUMNS.index("Avg_Temperature_C")
        if live_weather.get("temperature") is not None:
            t = float(live_weather["temperature"])
            features[temp_idx] = t
            features[CLIMATE_FEATURE_COLUMNS.index("Max_Temperature_C")] = t + 3.0
            features[CLIMATE_FEATURE_COLUMNS.index("Min_Temperature_C")] = t - 3.0
            features[CLIMATE_FEATURE_COLUMNS.index("Temperature_Range_C")] = 6.0

        if live_weather.get("humidity") is not None:
            features[CLIMATE_FEATURE_COLUMNS.index("Relative_Humidity_pct")] = float(live_weather["humidity"])

        if live_weather.get("precipitation") is not None:
            features[CLIMATE_FEATURE_COLUMNS.index("Precipitation_mm")] = float(live_weather["precipitation"])

        if live_weather.get("pressure") is not None:
            # open-meteo gives surface pressure in hPa. Model trained on kPa.
            features[CLIMATE_FEATURE_COLUMNS.index("Surface_Pressure_kPa")] = float(live_weather["pressure"]) / 10.0

        if live_weather.get("wind") is not None:
            w = float(live_weather["wind"]) * (1000 / 3600) # km/h to m/s
            features[CLIMATE_FEATURE_COLUMNS.index("Wind_Speed_10m_m_s")] = w
            features[CLIMATE_FEATURE_COLUMNS.index("Wind_Speed_50m_m_s")] = w * 1.2

    # Forecast the *next* month, keeping other climate normals from the latest observation.
    month_index = CLIMATE_FEATURE_COLUMNS.index("Month")
    if live_weather:
        now = datetime.now()
        next_month = now.month
        next_year = now.year
    else:
        latest_month = int(features[month_index])
        latest_year = int(float(latest["Year"]))
        next_month = (latest_month % 12) + 1
        next_year = latest_year + 1 if next_month == 1 else latest_year
    features[month_index] = float(next_month)

    district_code = artifact["district_encoder"].transform([district])[0]
    features.append(float(district_code))

    previous_cases = float(latest[CLIMATE_TARGET_COLUMN])
    lat, lon = float(latest["Latitude"]), float(latest["Longitude"])
    return np.array([features], dtype=float), previous_cases, lat, lon, next_year, next_month


@router.post(
    "/train/dengue",
    response_model=TrainDengueResponse,
    dependencies=[Depends(require_role("admin"))],
)
def train_dengue_model():
    result = train_dengue_prediction.train_and_store()
    metrics = result["metrics"]
    return TrainDengueResponse(
        decision_tree=RegressionMetrics(**metrics["decision_tree"]),
        random_forest=RegressionMetrics(**metrics["random_forest"]),
        xgboost=RegressionMetrics(**metrics["xgboost"]),
        best_model=result["best_model_name"],
        rows_trained_on=result["rows_trained_on"],
    )


@router.get(
    "/predict/district/{district}",
    response_model=DistrictRiskPoint,
    dependencies=[Depends(require_role("admin", "doctor", "receptionist"))],
)
def predict_district(district: str, db: Session = Depends(get_db)):
    artifact = _get_artifact()
    latest = artifact["latest_by_district"].get(district)
    lat_lon = (float(latest["Latitude"]), float(latest["Longitude"])) if latest else None
    
    live_weather = {}
    if lat_lon:
        live_weather = _fetch_live_weather_bulk([lat_lon]).get(lat_lon, {})

    X, previous_cases, lat, lon, next_year, next_month = _build_feature_row(artifact, district, live_weather)

    model = artifact["models"][artifact["best_model_name"]]
    predicted_cases = float(max(model.predict(X)[0], 0))
    risk_level = classify_risk(predicted_cases)

    create_district_alert(db, district, predicted_cases, risk_level)

    return DistrictRiskPoint(
        district=district,
        latitude=lat,
        longitude=lon,
        predicted_cases=round(predicted_cases, 1),
        previous_cases=previous_cases,
        risk_level=risk_level,
    )


@router.get(
    "/risk-map",
    response_model=list[DistrictRiskPoint],
    dependencies=[Depends(require_role("admin", "doctor", "receptionist"))],
)
def risk_map(db: Session = Depends(get_db)):
    artifact = _get_artifact()
    model = artifact["models"][artifact["best_model_name"]]
    districts = sorted(artifact["latest_by_district"].keys())

    lat_lon_pairs = []
    for district in districts:
        latest = artifact["latest_by_district"][district]
        lat_lon_pairs.append((float(latest["Latitude"]), float(latest["Longitude"])))

    live_weather_map = _fetch_live_weather_bulk(lat_lon_pairs)

    points = []
    for i, district in enumerate(districts):
        lat_lon = lat_lon_pairs[i]
        live_weather = live_weather_map.get(lat_lon, {})
        X, previous_cases, lat, lon, _, _ = _build_feature_row(artifact, district, live_weather)
        predicted_cases = float(max(model.predict(X)[0], 0))
        risk_level = classify_risk(predicted_cases)
        points.append(
            DistrictRiskPoint(
                district=district,
                latitude=lat,
                longitude=lon,
                predicted_cases=round(predicted_cases, 1),
                previous_cases=previous_cases,
                risk_level=risk_level,
            )
        )
    return points
