from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class EmployeeRecord:
    employee_id: str
    start_date: date
    end_date: date | None
    regretted_exit: bool
    hired_date: date | None
    offer_accepted_date: date | None
