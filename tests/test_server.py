import json
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def test_server_health_kpis_quality_and_hiring(tmp_path):
    db_path = tmp_path / "server1.db"
    proc = subprocess.Popen(
        [sys.executable, "-m", "hr_insights.server", "--host", "127.0.0.1", "--port", "8081"],
        env={"PYTHONPATH": "src", "HR_INSIGHTS_DB_PATH": str(db_path)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(0.5)
        for _ in range(2):
            with urlopen("http://127.0.0.1:8081/hiring-funnel?csv_path=data/sample_employees.csv", timeout=3) as response:
                funnel_payload = json.loads(response.read().decode("utf-8"))
                assert funnel_payload["applicants"] == 5

        with urlopen("http://127.0.0.1:8081/reports?type=hiring_funnel&limit=1&offset=0&created_after=1900-01-01T00:00:00%2B00:00", timeout=3) as response:
            first_page = json.loads(response.read().decode("utf-8"))
            assert len(first_page["reports"]) == 1
            assert "id" in first_page["reports"][0]

        with urlopen("http://127.0.0.1:8081/reports?type=hiring_funnel&limit=1&offset=1", timeout=3) as response:
            second_page = json.loads(response.read().decode("utf-8"))
            assert len(second_page["reports"]) == 1

        with urlopen("http://127.0.0.1:8081/reports/export?type=hiring_funnel&limit=5&offset=0", timeout=3) as response:
            export_body = response.read().decode("utf-8")
            assert "id,created_at,report_type,csv_path,as_of,payload_json" in export_body
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_server_enforces_api_key_and_readiness_probe(tmp_path):
    db_path = tmp_path / "server2.db"
    proc = subprocess.Popen(
        [sys.executable, "-m", "hr_insights.server", "--host", "127.0.0.1", "--port", "8082"],
        env={
            "PYTHONPATH": "src",
            "HR_INSIGHTS_DB_PATH": str(db_path),
            "HR_INSIGHTS_API_KEY": "topsecret",
            "HR_INSIGHTS_READINESS_CSV_PATH": "data/sample_employees.csv",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(0.5)
        try:
            urlopen("http://127.0.0.1:8082/kpis?csv_path=data/sample_employees.csv", timeout=3)
            raise AssertionError("Expected HTTPError for missing API key")
        except HTTPError as exc:
            assert exc.code == 401

        req = Request(
            "http://127.0.0.1:8082/kpis?csv_path=data/sample_employees.csv",
            headers={"X-API-Key": "topsecret"},
            method="GET",
        )
        with urlopen(req, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert payload["attrition_rate"] == 0.4
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_server_rejects_invalid_pagination_params(tmp_path):
    db_path = tmp_path / "server4.db"
    proc = subprocess.Popen([sys.executable, "-m", "hr_insights.server", "--host", "127.0.0.1", "--port", "8084"], env={"PYTHONPATH": "src", "HR_INSIGHTS_DB_PATH": str(db_path)}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        time.sleep(0.5)
        try:
            urlopen("http://127.0.0.1:8084/reports?limit=-1", timeout=3)
            raise AssertionError("Expected HTTPError for invalid limit")
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_server_protects_report_endpoints_with_api_key(tmp_path):
    db_path = tmp_path / "server5.db"
    proc = subprocess.Popen(
        [sys.executable, "-m", "hr_insights.server", "--host", "127.0.0.1", "--port", "8085"],
        env={"PYTHONPATH": "src", "HR_INSIGHTS_DB_PATH": str(db_path), "HR_INSIGHTS_API_KEY": "topsecret"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(0.5)
        try:
            urlopen("http://127.0.0.1:8085/reports", timeout=3)
            raise AssertionError("Expected HTTPError for missing API key")
        except HTTPError as exc:
            assert exc.code == 401

        req = Request("http://127.0.0.1:8085/reports", headers={"X-API-Key": "topsecret"}, method="GET")
        with urlopen(req, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert "reports" in payload
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_server_cleanup_rejects_invalid_json(tmp_path):
    db_path = tmp_path / "server6.db"
    proc = subprocess.Popen(
        [sys.executable, "-m", "hr_insights.server", "--host", "127.0.0.1", "--port", "8086"],
        env={"PYTHONPATH": "src", "HR_INSIGHTS_DB_PATH": str(db_path)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(0.5)
        req = Request(
            "http://127.0.0.1:8086/reports/cleanup",
            data=b"{not-valid-json",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(req, timeout=3)
            raise AssertionError("Expected HTTPError for invalid JSON")
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        proc.terminate()
        proc.wait(timeout=5)
