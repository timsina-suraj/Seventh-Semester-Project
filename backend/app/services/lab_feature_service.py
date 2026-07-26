"""Module 17: wires a patient's real lab_tests/lab_results into the dengue
risk model's feature set instead of relying purely on manually-typed values
on the prediction form. `LabResult.result_value` is a free-text field (e.g.
"186371 /uL", "Positive"), not a structured per-analyte number, so matching
is done by keyword in the test name plus a light parse of the result string
— inherently approximate given that data model, but real lab data beats a
guess whenever it's available, and untouched fields simply fall back to
whatever the caller already provided."""
from __future__ import annotations

import re

from app.models.lab_test import LabTest
from app.schemas.ml import PatientDiagnosisRequest

_NUMBER_RE = re.compile(r"-?\d+(\.\d+)?")


def _extract_number(result_value: str | None) -> float | None:
    if not result_value:
        return None
    match = _NUMBER_RE.search(result_value)
    return float(match.group()) if match else None


def _extract_positive(result_value: str | None) -> bool | None:
    if not result_value:
        return None
    lowered = result_value.lower()
    if "positive" in lowered:
        return True
    if "negative" in lowered:
        return False
    return None


def apply_lab_history(payload: PatientDiagnosisRequest, lab_tests: list[LabTest]) -> None:
    """Overrides the lab-trend/serology fields on `payload` in place with
    real completed results wherever a matching test exists for this
    patient. `day1`/`day3` are approximated as the earliest and latest
    completed result for that analyte — lab_tests has no "day of illness"
    concept, only when it was requested, so a patient with only one
    platelet/hematocrit test on file gets the same value for both
    (change-rate 0, honestly reflecting that no trend is visible yet).

    A combined test like "Dengue IgM/IgG" has one opaque result string for
    both antibodies, so it sets both `igm` and `igg` to the same
    positive/negative reading — a known simplification of the current
    single-result-per-test data model, not a bug."""
    completed = [t for t in lab_tests if t.status == "Completed" and t.result is not None]
    completed.sort(key=lambda t: t.result.completed_at)

    def series(keyword: str) -> list[LabTest]:
        return [t for t in completed if keyword in t.test_name.lower()]

    platelets = series("platelet")
    if platelets:
        first = _extract_number(platelets[0].result.result_value)
        last = _extract_number(platelets[-1].result.result_value)
        if first is not None:
            payload.platelet_day1 = int(first)
        if last is not None:
            payload.platelet_day3 = int(last)

    hematocrit = series("hematocrit")
    if hematocrit:
        first = _extract_number(hematocrit[0].result.result_value)
        last = _extract_number(hematocrit[-1].result.result_value)
        if first is not None:
            payload.hematocrit_day1 = first
        if last is not None:
            payload.hematocrit_day3 = last

    wbc = series("wbc")
    if wbc:
        value = _extract_number(wbc[-1].result.result_value)
        if value is not None:
            payload.wbc_count = int(value)

    for keyword, field in (("ns1", "ns1"), ("igg", "igg"), ("igm", "igm")):
        matches = series(keyword)
        if matches:
            positive = _extract_positive(matches[-1].result.result_value)
            if positive is not None:
                setattr(payload, field, positive)
