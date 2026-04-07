from hr_insights.config import AppConfig


def test_default_config_from_env(monkeypatch):
    monkeypatch.delenv("HR_INSIGHTS_HOST", raising=False)
    monkeypatch.delenv("HR_INSIGHTS_PORT", raising=False)
    monkeypatch.delenv("HR_INSIGHTS_LOG_LEVEL", raising=False)
    monkeypatch.delenv("HR_INSIGHTS_API_KEY", raising=False)
    monkeypatch.delenv("HR_INSIGHTS_READINESS_CSV_PATH", raising=False)
    monkeypatch.delenv("HR_INSIGHTS_RATE_LIMIT_PER_MINUTE", raising=False)
    monkeypatch.delenv("HR_INSIGHTS_DEFAULT_RETENTION_DAYS", raising=False)

    cfg = AppConfig.from_env()
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 8080
    assert cfg.log_level == "INFO"
    assert cfg.api_key is None
    assert cfg.readiness_csv_path is None
    assert cfg.rate_limit_per_minute == 0
    assert cfg.default_retention_days == 30


def test_override_config_from_env(monkeypatch):
    monkeypatch.setenv("HR_INSIGHTS_HOST", "127.0.0.1")
    monkeypatch.setenv("HR_INSIGHTS_PORT", "9090")
    monkeypatch.setenv("HR_INSIGHTS_LOG_LEVEL", "debug")
    monkeypatch.setenv("HR_INSIGHTS_API_KEY", "secret")
    monkeypatch.setenv("HR_INSIGHTS_READINESS_CSV_PATH", "data/sample_employees.csv")
    monkeypatch.setenv("HR_INSIGHTS_RATE_LIMIT_PER_MINUTE", "120")
    monkeypatch.setenv("HR_INSIGHTS_DEFAULT_RETENTION_DAYS", "14")

    cfg = AppConfig.from_env()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 9090
    assert cfg.log_level == "DEBUG"
    assert cfg.api_key == "secret"
    assert cfg.readiness_csv_path == "data/sample_employees.csv"
    assert cfg.rate_limit_per_minute == 120
    assert cfg.default_retention_days == 14
