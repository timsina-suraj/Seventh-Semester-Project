"""Dataset quality checks for ML training pipelines."""
import math
from dataclasses import dataclass, field


@dataclass
class DatasetQualityReport:
    total_records: int = 0
    valid_records: int = 0
    missing_values: int = 0
    duplicate_records: int = 0
    outliers: int = 0
    missing_columns: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "missing_values": self.missing_values,
            "duplicate_records": self.duplicate_records,
            "outliers": self.outliers,
            "missing_columns": self.missing_columns,
        }


def _is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def validate_dataset(
    rows: list[dict],
    required_columns: list[str],
    numeric_outlier_columns: list[str] | None = None,
) -> DatasetQualityReport:
    """Lightweight quality pass over a list-of-dicts dataset (e.g. csv.DictReader
    rows) before ML training. Outliers are flagged via a 3-sigma rule per column."""
    numeric_outlier_columns = numeric_outlier_columns or []
    report = DatasetQualityReport(total_records=len(rows))

    if rows:
        present_columns = set(rows[0].keys())
        report.missing_columns = [c for c in required_columns if c not in present_columns]

    missing_values = 0
    seen = set()
    duplicates = 0
    for row in rows:
        row_key = tuple(sorted(row.items()))
        if row_key in seen:
            duplicates += 1
        else:
            seen.add(row_key)
        for col in required_columns:
            if _is_missing(row.get(col)):
                missing_values += 1

    report.missing_values = missing_values
    report.duplicate_records = duplicates

    outliers = 0
    for col in numeric_outlier_columns:
        values = []
        for row in rows:
            v = row.get(col)
            try:
                values.append(float(v))
            except (TypeError, ValueError):
                continue
        if len(values) < 2:
            continue
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        if std == 0:
            continue
        for v in values:
            if abs(v - mean) > 3 * std:
                outliers += 1

    report.outliers = outliers
    report.valid_records = report.total_records - report.duplicate_records - (
        1 if report.missing_values > 0 else 0
    ) if report.total_records else 0
    report.valid_records = max(report.valid_records, 0)

    return report
