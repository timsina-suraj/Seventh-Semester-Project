"""GET /analytics response building — tested by calling the route function
directly (it has no DB/request dependencies, only reads trained model
artifacts from disk), matching the plain-function style already used for
app/ml/ training scripts in this test suite."""
from app.ml import train_dengue_prediction, train_diagnosis
from app.routers.analytics import get_analytics


def test_get_analytics_includes_feature_importance_for_best_model():
    train_diagnosis.train_and_store()
    train_dengue_prediction.train_and_store()

    result = get_analytics()

    assert "featureImportance" in result
    assert "bestDiagnosisModel" in result
    assert len(result["featureImportance"]) <= 10
    assert result["featureImportance"], "best model's importances should be populated after retraining"
    assert all("feature" in e and "importance" in e for e in result["featureImportance"])
    assert result["featureImportance"] == sorted(
        result["featureImportance"], key=lambda e: e["importance"], reverse=True
    )
    assert isinstance(result["bestDiagnosisModel"], str) and result["bestDiagnosisModel"]
