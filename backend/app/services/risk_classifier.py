from app.config import settings


def classify_risk(predicted_cases: float) -> str:
    if predicted_cases >= settings.risk_threshold_very_high:
        return "Very High"
    if predicted_cases >= settings.risk_threshold_high:
        return "High"
    if predicted_cases >= settings.risk_threshold_medium:
        return "Medium"
    return "Low"


def is_high_risk(risk_level: str) -> bool:
    return risk_level in ("High", "Very High")
