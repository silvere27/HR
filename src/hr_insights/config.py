from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"
    api_key: str | None = None
    readiness_csv_path: str | None = None
    rate_limit_per_minute: int = 0
    db_path: str = "hr_insights.db"
    default_retention_days: int = 30

    @staticmethod
    def from_env() -> "AppConfig":
        host = os.getenv("HR_INSIGHTS_HOST", "0.0.0.0")
        port = int(os.getenv("HR_INSIGHTS_PORT", "8080"))
        log_level = os.getenv("HR_INSIGHTS_LOG_LEVEL", "INFO").upper()
        api_key = os.getenv("HR_INSIGHTS_API_KEY")
        readiness_csv_path = os.getenv("HR_INSIGHTS_READINESS_CSV_PATH")
        rate_limit_per_minute = int(os.getenv("HR_INSIGHTS_RATE_LIMIT_PER_MINUTE", "0"))
        db_path = os.getenv("HR_INSIGHTS_DB_PATH", "hr_insights.db")
        default_retention_days = int(os.getenv("HR_INSIGHTS_DEFAULT_RETENTION_DAYS", "30"))
        return AppConfig(
            host=host,
            port=port,
            log_level=log_level,
            api_key=api_key,
            readiness_csv_path=readiness_csv_path,
            rate_limit_per_minute=rate_limit_per_minute,
            db_path=db_path,
            default_retention_days=default_retention_days,
        )
