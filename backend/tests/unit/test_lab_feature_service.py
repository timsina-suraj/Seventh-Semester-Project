"""apply_lab_history() only needs plain attribute access, so these tests
build LabTest/LabResult objects in memory without touching the DB."""
from datetime import datetime, timedelta, timezone

from app.models.lab_result import LabResult
from app.models.lab_test import LabTest
from app.schemas.ml import PatientDiagnosisRequest
from app.services.lab_feature_service import apply_lab_history

BASE_PAYLOAD_KWARGS = dict(
    gender="Female", age=30, days_since_fever_onset=2, body_temperature=39.0,
    platelet_day1=999, platelet_day3=999, hematocrit_day1=99.0, hematocrit_day3=99.0, wbc_count=999,
)


def _completed_test(test_name: str, result_value: str, completed_at: datetime) -> LabTest:
    test = LabTest(patient_id=1, doctor_id=1, test_name=test_name, status="Completed")
    test.result = LabResult(result_value=result_value, completed_at=completed_at)
    return test


def test_apply_lab_history_overrides_platelet_day1_and_day3_from_earliest_and_latest():
    now = datetime.now(timezone.utc)
    tests = [
        _completed_test("Platelet Count", "300000 /uL", now - timedelta(days=2)),
        _completed_test("Platelet Count", "90000 /uL", now),
    ]
    payload = PatientDiagnosisRequest(**BASE_PAYLOAD_KWARGS)

    apply_lab_history(payload, tests)

    assert payload.platelet_day1 == 300000
    assert payload.platelet_day3 == 90000


def test_apply_lab_history_uses_single_result_for_both_days_when_only_one_exists():
    now = datetime.now(timezone.utc)
    tests = [_completed_test("Hematocrit", "44.5", now)]
    payload = PatientDiagnosisRequest(**BASE_PAYLOAD_KWARGS)

    apply_lab_history(payload, tests)

    assert payload.hematocrit_day1 == 44.5
    assert payload.hematocrit_day3 == 44.5


def test_apply_lab_history_parses_serology_positive_negative():
    now = datetime.now(timezone.utc)
    tests = [
        _completed_test("Dengue NS1", "Positive", now),
        _completed_test("Dengue IgM/IgG", "Negative", now),
    ]
    payload = PatientDiagnosisRequest(**BASE_PAYLOAD_KWARGS, ns1=False, igg=True, igm=True)

    apply_lab_history(payload, tests)

    assert payload.ns1 is True
    # A combined IgM/IgG test has one result for both antibodies.
    assert payload.igg is False
    assert payload.igm is False


def test_apply_lab_history_ignores_uncompleted_tests():
    tests = [LabTest(patient_id=1, doctor_id=1, test_name="Platelet Count", status="Requested")]
    payload = PatientDiagnosisRequest(**BASE_PAYLOAD_KWARGS)

    apply_lab_history(payload, tests)

    assert payload.platelet_day1 == 999
    assert payload.platelet_day3 == 999


def test_apply_lab_history_leaves_payload_untouched_with_no_lab_tests():
    payload = PatientDiagnosisRequest(**BASE_PAYLOAD_KWARGS)

    apply_lab_history(payload, [])

    assert payload.platelet_day1 == 999
    assert payload.wbc_count == 999
    assert payload.ns1 is False


def test_apply_lab_history_ignores_unparseable_result_values():
    tests = [_completed_test("WBC Count", "inconclusive", datetime.now(timezone.utc))]
    payload = PatientDiagnosisRequest(**BASE_PAYLOAD_KWARGS)

    apply_lab_history(payload, tests)

    assert payload.wbc_count == 999
