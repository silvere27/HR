# HR

Initial implementation for the HR Data Insights PRD.

## Run KPI baseline calculator

```bash
PYTHONPATH=src python -m hr_insights.cli data/sample_employees.csv --as-of 2026-01-01
```

## JSON output

```bash
PYTHONPATH=src python -m hr_insights.cli data/sample_employees.csv --as-of 2026-01-01 --format json
```

## Data quality report

```bash
PYTHONPATH=src python -m hr_insights.cli data/sample_employees.csv --quality --format json
```

## Hiring funnel report

```bash
PYTHONPATH=src python -m hr_insights.cli data/sample_employees.csv --hiring-funnel --format json
```

## Run HTTP server

```bash
PYTHONPATH=src python -m hr_insights.server --host 127.0.0.1 --port 8081
```

Endpoints:
- `GET /health` (includes `version` and `uptime_seconds`)
- `GET /ready` (readiness check, optional CSV probe)
- `GET /metrics` (Prometheus-style counters)
- `GET/POST /kpis`
- `GET/POST /quality`
- `GET/POST /hiring-funnel`
- `GET /reports?type=<kpis|quality|hiring_funnel>&limit=50&offset=0&created_after=<ISO>&created_before=<ISO> (includes report `id`)` (persisted report history)
- `GET /reports/export?type=<kpis|quality|hiring_funnel>&limit=50&offset=0&created_after=<ISO>&created_before=<ISO>` (CSV export)
- `POST /reports/cleanup` with optional `{"retention_days": <int>}` payload

### Optional API key auth
Set `HR_INSIGHTS_API_KEY` to require `X-API-Key` on all endpoints except `/health`, `/ready`, and `/metrics`.

### Optional readiness CSV probe
Set `HR_INSIGHTS_READINESS_CSV_PATH` to validate CSV readability during `/ready` checks.

### Optional rate limit
Set `HR_INSIGHTS_RATE_LIMIT_PER_MINUTE` to enforce per-IP request throttling on report endpoints.

### Report persistence and retention
- `HR_INSIGHTS_DB_PATH`: SQLite database location.
- `HR_INSIGHTS_DEFAULT_RETENTION_DAYS`: fallback retention window for cleanup endpoint.

## Production readiness additions
- GitHub Actions CI workflow: `.github/workflows/ci.yml`
- Container runtime: `Dockerfile`
- Common developer commands: `Makefile`

## Run tests

```bash
make test
```


Parameter bounds:
- `limit`: 1..500
- `offset`: 0..1,000,000
- `retention_days`: 0..3650
