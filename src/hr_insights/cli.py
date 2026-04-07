import argparse

from .metrics import calculate_kpis, load_employee_records


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute baseline HR KPIs from CSV data.")
    parser.add_argument("csv_path", help="Path to employee CSV data")
    args = parser.parse_args()

    records = load_employee_records(args.csv_path)
    kpis = calculate_kpis(records)

    print("HR KPI Summary")
    print(f"- Attrition Rate: {kpis.attrition_rate:.2%}")
    print(f"- Regretted Attrition Rate: {kpis.regretted_attrition_rate:.2%}")
    print(f"- Median Time-to-Fill (days): {kpis.median_time_to_fill_days:.1f}")
    print(f"- Offer Acceptance Rate: {kpis.offer_acceptance_rate:.2%}")


if __name__ == "__main__":
    main()
