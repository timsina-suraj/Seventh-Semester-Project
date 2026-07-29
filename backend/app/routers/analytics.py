from fastapi import APIRouter, Depends, HTTPException

from app.ml import train_dengue_prediction, train_diagnosis
from app.security.rbac import require_role

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("", dependencies=[Depends(require_role("admin"))])
def get_analytics():
    dengue_artifact = train_dengue_prediction.load_artifact()
    diagnosis_artifact = train_diagnosis.load_artifact()

    if not dengue_artifact or not diagnosis_artifact:
        raise HTTPException(
            status_code=400,
            detail="Models not trained yet. Cannot fetch analytics."
        )

    # Format modelRegressionData
    model_regression_data = []
    for model_name, metrics in dengue_artifact["metrics"].items():
        # model_name is like "decision_tree" -> "Decision Tree"
        display_name = model_name.replace("_", " ").title()
        if display_name == "Xgboost":
            display_name = "XGBoost"
        model_regression_data.append({
            "model": display_name,
            "RMSE": round(metrics["rmse"], 2),
            "MAE": round(metrics["mae"], 2),
            "R² Score": round(metrics["r2"], 3)
        })

    # Format classificationData
    classification_data = []
    cm = None
    best_diagnosis_model = diagnosis_artifact["best_model_name"]
    
    for model_name, metrics in diagnosis_artifact["metrics"].items():
        display_name = model_name.replace("_", " ").title()
        if display_name == "Xgboost":
            display_name = "XGBoost"
            
        classification_data.append({
            "model": display_name,
            "Accuracy": round(metrics["accuracy"], 3),
            "Precision": round(metrics["precision"], 3),
            "Recall": round(metrics["recall"], 3),
            "F1": round(metrics["f1"], 3)
        })
        
        if model_name == best_diagnosis_model:
            cm = metrics.get("confusion_matrix", {"TP": 0, "FP": 0, "FN": 0, "TN": 0})

    feature_importance_list = diagnosis_artifact.get("feature_importance", {}).get(best_diagnosis_model, [])[:10]
    best_diagnosis_display = best_diagnosis_model.replace("_", " ").title()
    if best_diagnosis_display == "Xgboost":
        best_diagnosis_display = "XGBoost"

    return {
        "modelRegressionData": model_regression_data,
        "classificationData": classification_data,
        "CM": cm,
        "actualVsPredicted": dengue_artifact.get("actual_vs_predicted", []),
        "weatherData": dengue_artifact.get("weather_data", []),
        "diagnosisDist": diagnosis_artifact.get("diagnosis_dist", []),
        "symptomsData": diagnosis_artifact.get("symptoms_data", []),
        "featureImportance": feature_importance_list,
        "bestDiagnosisModel": best_diagnosis_display,
    }
