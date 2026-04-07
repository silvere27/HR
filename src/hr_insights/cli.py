import argparse
import json

from .service import KPIRequest, KPIService


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute baseline HR KPIs from CSV data.")
    parser.add_argument("csv_path", help="Path to employee CSV data")
    parser.add_argument(
        "--as-of",
        help="As-of date in YYYY-MM-DD format for attrition calculations (defaults to today)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--quality", action="store_true", help="Return data quality report instead of KPI report")
    mode_group.add_argument("--hiring-funnel", action="store_true", help="Return hiring funnel report")
    args = parser.parse_args()

    request = KPIRequest.from_strings(csv_path=args.csv_path, as_of=args.as_of)
    service = KPIService()

    if args.quality:
        quality_payload = service.quality_report_dict(request)
        if args.format == "json":
            print(json.dumps(quality_payload, indent=2, sort_keys=True))
            return
        print("HR Data Quality Summary")
        print(f"- Total Records: {quality_payload['total_records']}")
        print(f"- Missing Start Date Rate: {quality_payload['missing_start_date_rate']:.2%}")
        print(f"- Duplicate Employee ID Rate: {quality_payload['duplicate_employee_id_rate']:.2%}")
        print(f"- Missing Demographic Group Rate: {quality_payload['missing_demographic_group_rate']:.2%}")
        return

    if args.hiring_funnel:
        funnel_payload = service.hiring_funnel_report_dict(request)
        if args.format == "json":
            print(json.dumps(funnel_payload, indent=2, sort_keys=True))
            return
        print("Hiring Funnel Summary")
        print(f"- Applicants: {funnel_payload['applicants']}")
        print(f"- Screened: {funnel_payload['screened']}")
        print(f"- Interviewed: {funnel_payload['interviewed']}")
        print(f"- Offered: {funnel_payload['offered']}")
        print(f"- Hired: {funnel_payload['hired']}")
        print(f"- Screen Conversion: {funnel_payload['screen_conversion_rate']:.2%}")
        print(f"- Interview Conversion: {funnel_payload['interview_conversion_rate']:.2%}")
        print(f"- Offer Conversion: {funnel_payload['offer_conversion_rate']:.2%}")
        print(f"- Hire Conversion: {funnel_payload['hire_conversion_rate']:.2%}")
        return

    kpis = service.calculate(request)

    if args.format == "json":
        print(json.dumps(kpis.to_dict(), indent=2, sort_keys=True))
        return

    print("HR KPI Summary")
    print(f"- Attrition Rate: {kpis.attrition_rate:.2%}")
    print(f"- Regretted Attrition Rate: {kpis.regretted_attrition_rate:.2%}")
    print(f"- Median Time-to-Fill (days): {kpis.median_time_to_fill_days:.1f}")
    print(f"- Offer Acceptance Rate: {kpis.offer_acceptance_rate:.2%}")
    print(f"- Internal Mobility Rate: {kpis.internal_mobility_rate:.2%}")
    print("- Representation by Group:")
    for group, ratio in kpis.representation_by_group.items():
        print(f"  - {group}: {ratio:.2%}")


if __name__ == "__main__":
    main()
