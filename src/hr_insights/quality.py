from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import EmployeeRecord


@dataclass(frozen=True)
class DataQualityReport:
    total_records: int
    missing_start_date_rate: float
    duplicate_employee_id_rate: float
    missing_demographic_group_rate: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def assess_data_quality(records: list[EmployeeRecord]) -> DataQualityReport:
    if not records:
        raise ValueError("No employee records were provided.")

    total = len(records)
    missing_start_dates = len([r for r in records if r.start_date is None])

    seen: set[str] = set()
    duplicates = 0
    for record in records:
        if record.employee_id in seen:
            duplicates += 1
        seen.add(record.employee_id)

    missing_demo = len(
        [r for r in records if not r.demographic_group or r.demographic_group.strip().lower() in {"", "unknown"}]
    )

    return DataQualityReport(
        total_records=total,
        missing_start_date_rate=missing_start_dates / total,
        duplicate_employee_id_rate=duplicates / total,
        missing_demographic_group_rate=missing_demo / total,
    )
