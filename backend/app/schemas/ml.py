from pydantic import BaseModel, Field


class RegressionMetrics(BaseModel):
    mae: float
    rmse: float
    r2: float


class ClassificationMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float


class TrainDengueResponse(BaseModel):
    decision_tree: RegressionMetrics
    random_forest: RegressionMetrics
    xgboost: RegressionMetrics
    best_model: str
    rows_trained_on: int


class TrainDiagnosisResponse(BaseModel):
    decision_tree: ClassificationMetrics
    random_forest: ClassificationMetrics
    xgboost: ClassificationMetrics
    best_model: str
    rows_trained_on: int


class DistrictRiskPoint(BaseModel):
    district: str
    latitude: float
    longitude: float
    predicted_cases: float
    previous_cases: float | None
    risk_level: str


class PatientDiagnosisRequest(BaseModel):
    gender: str
    age: int = Field(ge=0, le=120)
    fever_duration: int = Field(ge=0, le=30)
    body_temperature: float = Field(ge=35.0, le=42.0)
    platelet_count: int = Field(gt=0)
    wbc_count: int = Field(gt=0)
    joint_pain: str  # None / Moderate / Severe
    headache: bool
    retro_orbital_pain: bool
    myalgia: bool
    rash: bool
    patient_id: int | None = None


class PatientDiagnosisResponse(BaseModel):
    dengue_positive: bool
    probability: float
    model_used: str
    severity_hint: str
