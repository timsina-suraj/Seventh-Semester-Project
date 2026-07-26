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
    district: str = ""
    visit_month: str = ""
    days_since_fever_onset: int = Field(ge=0, le=30)
    body_temperature: float = Field(ge=35.0, le=42.0)

    # Lab-trend values (day 1 and day 3 of illness) — the model derives the
    # change-rate itself, mirroring the dataset's precomputed columns.
    platelet_day1: int = Field(gt=0)
    platelet_day3: int = Field(gt=0)
    hematocrit_day1: float = Field(gt=0)
    hematocrit_day3: float = Field(gt=0)
    wbc_count: int = Field(gt=0)

    # Rapid serology (leave false if not tested yet)
    ns1: bool = False
    igg: bool = False
    igm: bool = False

    joint_pain: str = "No_Joint_Pain"  # No_Joint_Pain / Moderate / Severe
    headache: bool = False
    retro_orbital_pain: bool = False
    myalgia: bool = False
    rash: bool = False

    # WHO warning signs
    persistent_vomiting: bool = False
    abdominal_pain: bool = False
    bleeding: bool = False
    restlessness: bool = False
    lethargy: bool = False
    liver_enlargement: bool = False

    # Comorbidities
    previous_dengue_history: bool = False
    diabetes: bool = False
    hypertension: bool = False
    obesity: bool = False
    pregnancy: bool = False

    patient_id: int | None = None


class PatientDiagnosisResponse(BaseModel):
    dengue_positive: bool
    probability: float
    model_used: str
    severity_hint: str
    warning_sign_count: int
