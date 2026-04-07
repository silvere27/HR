from hr_insights.metrics import load_employee_records
from hr_insights.quality import assess_data_quality


def test_quality_report_from_sample_data():
    rows = load_employee_records("data/sample_employees.csv")
    report = assess_data_quality(rows)

    assert report.total_records == 5
    assert report.missing_start_date_rate == 0.0
    assert report.duplicate_employee_id_rate == 0.0
    assert report.missing_demographic_group_rate == 0.0
