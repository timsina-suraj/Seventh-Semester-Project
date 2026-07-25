from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml import train_diagnosis
from app.ml.preprocessing import encode_single_patient
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.schemas.ml import (
    ClassificationMetrics,
    PatientDiagnosisRequest,
    PatientDiagnosisResponse,
    TrainDiagnosisResponse,
)
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.alert_service import create_patient_diagnosis_alert

router = APIRouter(prefix="/ml", tags=["ml-diagnosis"])


def _severity_hint(payload: PatientDiagnosisRequest) -> str:
    """A simple clinical-triage heuristic (not the ML model itself) used to
    prioritize doctor follow-up, mirroring the spec's Severe/Moderate/Mild
    labels used elsewhere in the symptom dataset."""
    warning_signs = sum([payload.retro_orbital_pain, payload.rash, payload.myalgia])
    if payload.platelet_count < 50_000 or (payload.platelet_count < 100_000 and warning_signs >= 2):
        return "Severe"
    if payload.platelet_count < 150_000 or warning_signs >= 1:
        return "Moderate"
    return "Mild"


@router.post(
    "/train/diagnosis",
    response_model=TrainDiagnosisResponse,
    dependencies=[Depends(require_role("admin"))],
)
def train_diagnosis_model():
    result = train_diagnosis.train_and_store()
    metrics = result["metrics"]
    return TrainDiagnosisResponse(
        decision_tree=ClassificationMetrics(**metrics["decision_tree"]),
        random_forest=ClassificationMetrics(**metrics["random_forest"]),
        xgboost=ClassificationMetrics(**metrics["xgboost"]),
        best_model=result["best_model_name"],
        rows_trained_on=result["rows_trained_on"],
    )


@router.post(
    "/predict/patient",
    response_model=PatientDiagnosisResponse,
    dependencies=[Depends(require_role("admin", "doctor", "patient"))],
)
def predict_patient(
    payload: PatientDiagnosisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    artifact = train_diagnosis.load_artifact()
    if artifact is None:
        raise HTTPException(
            status_code=400,
            detail="Diagnosis model has not been trained yet. Call POST /ml/train/diagnosis first.",
        )

    model = artifact["models"][artifact["best_model_name"]]
    X = encode_single_patient(payload.model_dump())
    probability = float(model.predict_proba(X)[0][1])
    dengue_positive = probability >= 0.5
    severity = _severity_hint(payload)
    
    district = None
    from app.models.patient import Patient
    
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if patient:
            payload.patient_id = patient.id
            district = patient.district
    else:
        if payload.patient_id:
            p = db.query(Patient).filter(Patient.id == payload.patient_id).first()
            if p:
                district = p.district

    if payload.patient_id is not None:
        record = MedicalRecord(
            patient_id=payload.patient_id,
            encrypted_symptoms=(
                f"joint_pain={payload.joint_pain}, headache={payload.headache}, "
                f"retro_orbital_pain={payload.retro_orbital_pain}, myalgia={payload.myalgia}, rash={payload.rash}"
            ),
            encrypted_diagnosis="Dengue Positive" if dengue_positive else "Dengue Negative",
            encrypted_lab_result=(
                f"Platelets={payload.platelet_count} WBC={payload.wbc_count}"
            ),
            ml_dengue_predicted=dengue_positive,
            ml_dengue_probability=probability,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        if dengue_positive:
            create_patient_diagnosis_alert(db, district=district, severity=severity, patient_id=payload.patient_id)

    return PatientDiagnosisResponse(
        dengue_positive=dengue_positive,
        probability=round(probability, 4),
        model_used=artifact["best_model_name"],
        severity_hint=severity,
    )
