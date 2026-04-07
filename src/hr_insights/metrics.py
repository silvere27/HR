from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from statistics import median
from typing import Iterable

from .models import EmployeeRecord


@dataclass(frozen=True)
class KPIResult:
    attrition_rate: float
    regretted_attrition_rate: float
    median_time_to_fill_days: float
    offer_acceptance_rate: float


def _parse_date(raw: str) -> date | None:
    raw = raw.strip()
    if not raw:
        return None
    return datetime.strptime(raw, "%Y-%m-%d").date()


def load_employee_records(csv_path: str) -> list[EmployeeRecord]:
    records: list[EmployeeRecord] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            records.append(
                EmployeeRecord(
                    employee_id=row["employee_id"],
                    start_date=_parse_date(row["start_date"]) or date.today(),
                    end_date=_parse_date(row["end_date"]),
                    regretted_exit=row["regretted_exit"].strip().lower() == "true",
                    hired_date=_parse_date(row.get("hired_date", "")),
                    offer_accepted_date=_parse_date(row.get("offer_accepted_date", "")),
                )
            )
    return records


def calculate_kpis(records: Iterable[EmployeeRecord]) -> KPIResult:
    rows = list(records)
    if not rows:
        raise ValueError("No employee records were provided.")

    exits = [r for r in rows if r.end_date is not None]
    regretted_exits = [r for r in exits if r.regretted_exit]

    avg_headcount = len(rows)
    attrition_rate = len(exits) / avg_headcount
    regretted_attrition_rate = len(regretted_exits) / avg_headcount

    time_to_fill_values = [
        (r.offer_accepted_date - r.hired_date).days
        for r in rows
        if r.offer_accepted_date is not None and r.hired_date is not None
    ]
    median_time_to_fill_days = float(median(time_to_fill_values)) if time_to_fill_values else 0.0

    offers_extended = len([r for r in rows if r.hired_date is not None])
    offers_accepted = len([r for r in rows if r.offer_accepted_date is not None])
    offer_acceptance_rate = (offers_accepted / offers_extended) if offers_extended else 0.0

    return KPIResult(
        attrition_rate=attrition_rate,
        regretted_attrition_rate=regretted_attrition_rate,
        median_time_to_fill_days=median_time_to_fill_days,
        offer_acceptance_rate=offer_acceptance_rate,
    )
