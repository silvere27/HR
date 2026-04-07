from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import EmployeeRecord


@dataclass(frozen=True)
class HiringFunnelReport:
    applicants: int
    screened: int
    interviewed: int
    offered: int
    hired: int
    screen_conversion_rate: float
    interview_conversion_rate: float
    offer_conversion_rate: float
    hire_conversion_rate: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def assess_hiring_funnel(records: list[EmployeeRecord]) -> HiringFunnelReport:
    if not records:
        raise ValueError("No employee records were provided.")

    applicants = len([r for r in records if r.applicant_date is not None])
    screened = len([r for r in records if r.screened_date is not None])
    interviewed = len([r for r in records if r.interviewed_date is not None])
    offered = len([r for r in records if r.offered_date is not None])
    hired = len([r for r in records if r.offer_accepted_date is not None])

    return HiringFunnelReport(
        applicants=applicants,
        screened=screened,
        interviewed=interviewed,
        offered=offered,
        hired=hired,
        screen_conversion_rate=(screened / applicants) if applicants else 0.0,
        interview_conversion_rate=(interviewed / screened) if screened else 0.0,
        offer_conversion_rate=(offered / interviewed) if interviewed else 0.0,
        hire_conversion_rate=(hired / offered) if offered else 0.0,
    )
