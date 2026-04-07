from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .hiring import HiringFunnelReport, assess_hiring_funnel
from .metrics import KPIResult, calculate_kpis, load_employee_records
from .quality import DataQualityReport, assess_data_quality


@dataclass(frozen=True)
class KPIRequest:
    csv_path: str
    as_of: date | None = None

    @staticmethod
    def from_strings(csv_path: str, as_of: str | None) -> "KPIRequest":
        parsed_as_of = datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else None
        return KPIRequest(csv_path=csv_path, as_of=parsed_as_of)


class KPIService:
    """Application service for KPI calculations.

    Encapsulates loading and calculation so CLI/API layers remain thin.
    """

    def calculate(self, request: KPIRequest) -> KPIResult:
        records = load_employee_records(request.csv_path)
        return calculate_kpis(records, as_of=request.as_of)

    def calculate_dict(self, request: KPIRequest) -> dict[str, float]:
        return self.calculate(request).to_dict()

    def quality_report(self, request: KPIRequest) -> DataQualityReport:
        records = load_employee_records(request.csv_path)
        return assess_data_quality(records)

    def quality_report_dict(self, request: KPIRequest) -> dict[str, float | int]:
        return self.quality_report(request).to_dict()

    def hiring_funnel_report(self, request: KPIRequest) -> HiringFunnelReport:
        records = load_employee_records(request.csv_path)
        return assess_hiring_funnel(records)

    def hiring_funnel_report_dict(self, request: KPIRequest) -> dict[str, float | int]:
        return self.hiring_funnel_report(request).to_dict()
