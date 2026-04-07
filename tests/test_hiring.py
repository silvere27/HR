from hr_insights.hiring import assess_hiring_funnel
from hr_insights.metrics import load_employee_records


def test_hiring_funnel_from_sample_data():
    rows = load_employee_records("data/sample_employees.csv")
    report = assess_hiring_funnel(rows)

    assert report.applicants == 5
    assert report.screened == 5
    assert report.interviewed == 5
    assert report.offered == 5
    assert report.hired == 4
    assert report.hire_conversion_rate == 0.8
