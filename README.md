# HR

Initial implementation for the HR Data Insights PRD.

## Run KPI baseline calculator

```bash
PYTHONPATH=src python -m hr_insights.cli data/sample_employees.csv
```

## Sample output

- Attrition Rate
- Regretted Attrition Rate
- Median Time-to-Fill
- Offer Acceptance Rate
# HR Management System

This repository contains a simple HR management script for calculating employee payroll.

## Setup

No special setup is required. You only need to have Python installed on your system.

## Usage

To use the `calculate_payroll` function, you can import it into your Python script:

```python
from hr import calculate_payroll

total_payroll = calculate_payroll(hours_worked=40, hourly_rate=25)
print(f"Total payroll: ${total_payroll}")
```
