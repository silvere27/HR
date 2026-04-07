from hr_insights.service import KPIRequest, KPIService


def test_service_calculates_payload():
    service = KPIService()
    request = KPIRequest.from_strings("data/sample_employees.csv", "2026-01-01")
    payload = service.calculate_dict(request)

    assert payload["attrition_rate"] == 0.4
    assert payload["regretted_attrition_rate"] == 0.2
    assert payload["median_time_to_fill_days"] == 21.5
    assert payload["offer_acceptance_rate"] == 0.8
    assert payload["internal_mobility_rate"] == 0.4
    assert payload["representation_by_group"]["men"] == 0.4
