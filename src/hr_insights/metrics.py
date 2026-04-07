from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
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
    internal_mobility_rate: float
    representation_by_group: dict[str, float]

    def to_dict(self) -> dict:
        return asdict(self)


def _parse_date(raw: str) -> date | None:
    value = raw.strip()
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_bool(raw: str) -> bool:
    value = raw.strip().lower()
    if value in {"true", "1", "yes", "y"}:
        return True
    if value in {"false", "0", "no", "n", ""}:
        return False
    raise ValueError(f"Invalid boolean value: {raw}")


def load_employee_records(csv_path: str) -> list[EmployeeRecord]:
    records: list[EmployeeRecord] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required_columns = {
            "employee_id",
            "start_date",
            "end_date",
            "regretted_exit",
            "hired_date",
            "offer_accepted_date",
        }
        if reader.fieldnames is None or not required_columns.issubset(set(reader.fieldnames)):
            missing = required_columns.difference(set(reader.fieldnames or []))
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        for row in reader:
            start_date = _parse_date(row["start_date"])
            if start_date is None:
                raise ValueError(f"start_date is required for employee_id={row['employee_id']}")

            records.append(
                EmployeeRecord(
                    employee_id=row["employee_id"].strip(),
                    start_date=start_date,
                    end_date=_parse_date(row["end_date"]),
                    regretted_exit=_parse_bool(row["regretted_exit"]),
                    hired_date=_parse_date(row["hired_date"]),
                    offer_accepted_date=_parse_date(row["offer_accepted_date"]),
                    promoted=_parse_bool(row.get("promoted", "")),
                    transferred=_parse_bool(row.get("transferred", "")),
                    demographic_group=(row.get("demographic_group", "unknown") or "unknown").strip().lower(),
                    applicant_date=_parse_date(row.get("applicant_date", "")),
                    screened_date=_parse_date(row.get("screened_date", "")),
                    interviewed_date=_parse_date(row.get("interviewed_date", "")),
                    offered_date=_parse_date(row.get("offered_date", "")),
                )
            )
    return records


def calculate_kpis(records: Iterable[EmployeeRecord], *, as_of: date | None = None) -> KPIResult:
    rows = list(records)
    if not rows:
        raise ValueError("No employee records were provided.")

    as_of_date = as_of or date.today()

    active_employees = [r for r in rows if r.start_date <= as_of_date and (r.end_date is None or r.end_date >= as_of_date)]
    exits = [r for r in rows if r.end_date is not None and r.end_date <= as_of_date]
    regretted_exits = [r for r in exits if r.regretted_exit]

    population = len(active_employees) + len(exits)
    if population == 0:
        raise ValueError("No records are valid for the selected as_of date.")

    attrition_rate = len(exits) / population
    regretted_attrition_rate = len(regretted_exits) / population

    time_to_fill_values = [
        (r.offer_accepted_date - r.hired_date).days
        for r in rows
        if r.offer_accepted_date is not None and r.hired_date is not None and r.offer_accepted_date >= r.hired_date
    ]
    median_time_to_fill_days = float(median(time_to_fill_values)) if time_to_fill_values else 0.0

    offers_extended = len([r for r in rows if r.hired_date is not None])
    offers_accepted = len([r for r in rows if r.offer_accepted_date is not None])
    offer_acceptance_rate = (offers_accepted / offers_extended) if offers_extended else 0.0

    internal_moves = len([r for r in rows if r.promoted or r.transferred])
    internal_mobility_rate = internal_moves / population

    representation_counts: dict[str, int] = {}
    for row in rows:
        representation_counts[row.demographic_group] = representation_counts.get(row.demographic_group, 0) + 1
    representation_by_group = {
        group: count / population
        for group, count in sorted(representation_counts.items())
    }

    return KPIResult(
        attrition_rate=attrition_rate,
        regretted_attrition_rate=regretted_attrition_rate,
        median_time_to_fill_days=median_time_to_fill_days,
        offer_acceptance_rate=offer_acceptance_rate,
        internal_mobility_rate=internal_mobility_rate,
        representation_by_group=representation_by_group,
    )
