from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_lab_test_repository, get_patient_repository
from app.ml import train_diagnosis
from app.ml.preprocessing import WHO_WARNING_SIGN_COLUMNS, encode_single_patient
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User
from app.repositories.lab_test_repository import LabTestRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.ml import (
    ClassificationMetrics,
    PatientDiagnosisRequest,
    PatientDiagnosisResponse,
    TrainDiagnosisResponse,
)
from app.security.auth import get_current_user
from app.security.rbac import require_role
from app.services.alert_service import create_patient_diagnosis_alert
from app.services.lab_feature_service import apply_lab_history

router = APIRouter(prefix="/ml", tags=["ml-diagnosis"])

_WARNING_SIGN_FIELDS = [col.lower() for col in WHO_WARNING_SIGN_COLUMNS]


def _warning_sign_count(payload: PatientDiagnosisRequest) -> int:
    return sum(1 for field in _WARNING_SIGN_FIELDS if getattr(payload, field))


def _severity_hint(payload: PatientDiagnosisRequest, warning_signs: int) -> str:
    """WHO dengue severity grading, approximated from warning signs +
    plasma-leakage lab trend (falling platelets by day 3) — not the ML model
    itself, used to prioritize doctor follow-up."""
    if payload.bleeding or payload.platelet_day3 < 50_000 or warning_signs >= 3:
        return "Severe"
    if warning_signs >= 1 or payload.platelet_day3 < 100_000:
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
async def predict_patient(
    payload: PatientDiagnosisRequest,
    db: AsyncSession = Depends(get_db),
    patient_repo: PatientRepository = Depends(get_patient_repository),
    lab_test_repo: LabTestRepository = Depends(get_lab_test_repository),
    current_user: User = Depends(get_current_user),
):
    artifact = train_diagnosis.load_artifact()
    if artifact is None:
        raise HTTPException(
            status_code=400,
            detail="Diagnosis model has not been trained yet. Call POST /ml/train/diagnosis first.",
        )

    district = None
    if current_user.role == "patient":
        patient = await patient_repo.get_by_user_id(current_user.id)
        if patient:
            payload.patient_id = patient.id
            district = patient.district
    else:
        if payload.patient_id:
            p = await db.get(Patient, payload.patient_id)
            if p:
                district = p.district
    if not payload.district and district:
        payload.district = district

    if payload.patient_id is not None:
        # Real lab data overrides manually-typed guesses wherever it's
        # available — see lab_feature_service for the matching rules.
        lab_tests = await lab_test_repo.list_filtered(patient_id=payload.patient_id, status="Completed")
        apply_lab_history(payload, lab_tests)

    model = artifact["models"][artifact["best_model_name"]]
    X = encode_single_patient(payload.model_dump(), artifact["district_encoder"])
    probability = float(model.predict_proba(X)[0][1])
    dengue_positive = probability >= 0.5
    warning_signs = _warning_sign_count(payload)
    severity = _severity_hint(payload, warning_signs)

    if payload.patient_id is not None:
        active_warning_signs = [f.replace("_", " ") for f in _WARNING_SIGN_FIELDS if getattr(payload, f)]
        record = MedicalRecord(
            patient_id=payload.patient_id,
            encrypted_symptoms=(
                f"joint_pain={payload.joint_pain}, headache={payload.headache}, "
                f"retro_orbital_pain={payload.retro_orbital_pain}, myalgia={payload.myalgia}, rash={payload.rash}, "
                f"warning_signs={', '.join(active_warning_signs) or 'none'}"
            ),
            encrypted_diagnosis="Dengue Positive" if dengue_positive else "Dengue Negative",
            encrypted_notes=(
                f"AI screening — Platelets(day1/day3)={payload.platelet_day1}/{payload.platelet_day3} "
                f"Hematocrit(day1/day3)={payload.hematocrit_day1}/{payload.hematocrit_day3} "
                f"WBC={payload.wbc_count} NS1={payload.ns1} IgG={payload.igg} IgM={payload.igm} "
                f"Severity={severity}"
            ),
            ml_dengue_predicted=dengue_positive,
            ml_dengue_probability=probability,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        if dengue_positive:
            await create_patient_diagnosis_alert(db, district=district, severity=severity, patient_id=payload.patient_id)

    return PatientDiagnosisResponse(
        dengue_positive=dengue_positive,
        probability=round(probability, 4),
        model_used=artifact["best_model_name"],
        severity_hint=severity,
        warning_sign_count=warning_signs,
    )
