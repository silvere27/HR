PYTHONPATH=src

.PHONY: test run-api run-kpi run-quality run-funnel

test:
	PYTHONPATH=$(PYTHONPATH) python -m pytest -q

run-api:
	PYTHONPATH=$(PYTHONPATH) python -m hr_insights.server --host 127.0.0.1 --port 8081

run-kpi:
	PYTHONPATH=$(PYTHONPATH) python -m hr_insights.cli data/sample_employees.csv --as-of 2026-01-01

run-quality:
	PYTHONPATH=$(PYTHONPATH) python -m hr_insights.cli data/sample_employees.csv --quality --format json

run-funnel:
	PYTHONPATH=$(PYTHONPATH) python -m hr_insights.cli data/sample_employees.csv --hiring-funnel --format json
