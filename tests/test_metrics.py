import json
import subprocess
import sys
from datetime import date

from hr_insights.metrics import calculate_kpis, load_employee_records


def test_load_records_and_calculate_kpis():
    records = load_employee_records("data/sample_employees.csv")
    result = calculate_kpis(records, as_of=date(2026, 1, 1))

    assert len(records) == 5
    assert round(result.attrition_rate, 3) == 0.4
    assert round(result.regretted_attrition_rate, 3) == 0.2
    assert round(result.median_time_to_fill_days, 1) == 21.5
    assert round(result.offer_acceptance_rate, 2) == 0.8
    assert round(result.internal_mobility_rate, 2) == 0.4
    assert result.representation_by_group["women"] == 0.4


def test_empty_records_raises_error():
    try:
        calculate_kpis([], as_of=date(2026, 1, 1))
    except ValueError as exc:
        assert "No employee records" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty records")


def test_cli_json_output():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hr_insights.cli",
            "data/sample_employees.csv",
            "--as-of",
            "2026-01-01",
            "--format",
            "json",
        ],
        check=True,
        capture_output=True,
        text=True,
        env={"PYTHONPATH": "src"},
    )
    payload = json.loads(completed.stdout)
    assert payload["attrition_rate"] == 0.4
    assert payload["offer_acceptance_rate"] == 0.8
    assert payload["internal_mobility_rate"] == 0.4
    assert payload["representation_by_group"]["non_binary"] == 0.2
