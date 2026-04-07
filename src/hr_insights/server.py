from __future__ import annotations

import argparse
import json
import logging
import threading
import time
import uuid
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__
from .config import AppConfig
from .metrics import load_employee_records
from .service import KPIRequest, KPIService
from .storage import ReportStore

LOGGER = logging.getLogger("hr_insights.server")
SERVER_START_TIME = time.time()


class KPIHandler(BaseHTTPRequestHandler):
    service = KPIService()
    config = AppConfig.from_env()
    store = ReportStore(config.db_path)
    request_count = 0
    error_count = 0
    _counter_lock = threading.Lock()
    _rate_lock = threading.Lock()
    _requests_by_ip: dict[str, deque[float]] = {}

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        LOGGER.info("%s - %s", self.address_string(), format % args)

    @classmethod
    def _inc_request(cls) -> None:
        with cls._counter_lock:
            cls.request_count += 1

    @classmethod
    def _inc_error(cls) -> None:
        with cls._counter_lock:
            cls.error_count += 1

    def _parse_bounded_int(self, value: str, *, name: str, min_value: int, max_value: int) -> int:
        try:
            parsed = int(value)
        except ValueError as exc:
            raise ValueError(f"Invalid integer for {name}: {value}") from exc
        if parsed < min_value or parsed > max_value:
            raise ValueError(f"{name} must be between {min_value} and {max_value}")
        return parsed

    def _is_rate_limited(self) -> bool:
        limit = self.config.rate_limit_per_minute
        if limit <= 0:
            return False

        ip = self.client_address[0]
        now = time.time()
        cutoff = now - 60
        with self._rate_lock:
            queue = self._requests_by_ip.setdefault(ip, deque())
            while queue and queue[0] < cutoff:
                queue.popleft()
            if len(queue) >= limit:
                return True
            queue.append(now)
        return False

    def _send_json(self, status: int, payload: dict, request_id: str | None = None) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if request_id:
            self.send_header("X-Request-ID", request_id)
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: int, body_text: str, content_type: str = "text/plain; charset=utf-8") -> None:
        body = body_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _is_authorized(self) -> bool:
        if not self.config.api_key:
            return True
        provided = self.headers.get("X-API-Key")
        return provided == self.config.api_key

    def _handle_payload(self, path: str, csv_path: str | None, as_of: str | None, request_id: str) -> None:
        if not csv_path:
            self._inc_error()
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Missing required parameter: csv_path"}, request_id=request_id)
            return

        try:
            request = KPIRequest.from_strings(csv_path=csv_path, as_of=as_of)
            if path == "/kpis":
                payload = self.service.calculate_dict(request)
                report_type = "kpis"
            elif path == "/quality":
                payload = self.service.quality_report_dict(request)
                report_type = "quality"
            elif path == "/hiring-funnel":
                payload = self.service.hiring_funnel_report_dict(request)
                report_type = "hiring_funnel"
            else:
                self._inc_error()
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"}, request_id=request_id)
                return

            self.store.save_report(report_type=report_type, csv_path=csv_path, as_of=as_of, payload=payload)
        except Exception as exc:
            self._inc_error()
            LOGGER.exception("Failed request request_id=%s path=%s", request_id, path)
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)}, request_id=request_id)
            return

        self._send_json(HTTPStatus.OK, payload, request_id=request_id)

    def _handle_reports_list(self, request_id: str, report_type: str | None, limit: int, offset: int, created_after: str | None, created_before: str | None) -> None:
        try:
            rows = self.store.list_reports(report_type=report_type, limit=limit, offset=offset, created_after=created_after, created_before=created_before)
        except Exception as exc:
            self._inc_error()
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)}, request_id=request_id)
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "reports": [
                    {
                        "id": r.id,
                        "created_at": r.created_at,
                        "report_type": r.report_type,
                        "csv_path": r.csv_path,
                        "as_of": r.as_of,
                        "payload": r.payload,
                    }
                    for r in rows
                ]
            },
            request_id=request_id,
        )

    def _handle_reports_export(self, report_type: str | None, limit: int, offset: int, created_after: str | None, created_before: str | None) -> None:
        try:
            csv_data = self.store.list_reports_csv(report_type=report_type, limit=limit, offset=offset, created_after=created_after, created_before=created_before)
        except Exception as exc:
            self._inc_error()
            self._send_text(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        self._send_text(HTTPStatus.OK, csv_data, content_type="text/csv; charset=utf-8")

    def _handle_reports_cleanup(self, request_id: str, retention_days: int) -> None:
        try:
            deleted = self.store.cleanup_old_reports(retention_days=retention_days)
        except Exception as exc:
            self._inc_error()
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)}, request_id=request_id)
            return
        self._send_json(HTTPStatus.OK, {"deleted_rows": deleted, "retention_days": retention_days}, request_id=request_id)

    def _read_json_body(self, request_id: str) -> dict | None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b""
        if not raw_body:
            return {}
        try:
            return json.loads(raw_body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._inc_error()
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body"}, request_id=request_id)
            return None

    def _handle_ready(self, request_id: str) -> None:
        csv_path = self.config.readiness_csv_path
        if not csv_path:
            self._send_json(HTTPStatus.OK, {"status": "ready", "check": "no_csv_probe"}, request_id=request_id)
            return
        try:
            load_employee_records(csv_path)
        except Exception as exc:
            self._inc_error()
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"status": "not_ready", "error": str(exc)}, request_id=request_id)
            return

        self._send_json(HTTPStatus.OK, {"status": "ready", "check": "csv_probe_ok"}, request_id=request_id)

    def do_GET(self) -> None:  # noqa: N802
        self._inc_request()
        request_id = uuid.uuid4().hex
        start = time.perf_counter()
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json(
                HTTPStatus.OK,
                {"status": "ok", "version": __version__, "uptime_seconds": round(time.time() - SERVER_START_TIME, 3)},
                request_id=request_id,
            )
            return

        if parsed.path == "/ready":
            self._handle_ready(request_id)
            return

        if parsed.path == "/metrics":
            self._send_text(
                HTTPStatus.OK,
                "\n".join(
                    [
                        "# HELP hr_insights_requests_total Total number of HTTP requests.",
                        "# TYPE hr_insights_requests_total counter",
                        f"hr_insights_requests_total {self.request_count}",
                        "# HELP hr_insights_errors_total Total number of handled errors.",
                        "# TYPE hr_insights_errors_total counter",
                        f"hr_insights_errors_total {self.error_count}",
                    ]
                )
                + "\n",
                content_type="text/plain; version=0.0.4",
            )
            return

        if parsed.path == "/reports":
            if self._is_rate_limited():
                self._inc_error()
                self._send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"}, request_id=request_id)
                return

            if not self._is_authorized():
                self._inc_error()
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"}, request_id=request_id)
                return
            query = parse_qs(parsed.query)
            report_type = query.get("type", [None])[0]
            try:
                limit = self._parse_bounded_int(query.get("limit", ["50"])[0], name="limit", min_value=1, max_value=500)
                offset = self._parse_bounded_int(query.get("offset", ["0"])[0], name="offset", min_value=0, max_value=1000000)
            except ValueError as exc:
                self._inc_error()
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)}, request_id=request_id)
                return
            created_after = query.get("created_after", [None])[0]
            created_before = query.get("created_before", [None])[0]
            self._handle_reports_list(request_id=request_id, report_type=report_type, limit=limit, offset=offset, created_after=created_after, created_before=created_before)
            return

        if parsed.path == "/reports/export":
            if self._is_rate_limited():
                self._inc_error()
                self._send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"}, request_id=request_id)
                return

            if not self._is_authorized():
                self._inc_error()
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"}, request_id=request_id)
                return
            query = parse_qs(parsed.query)
            report_type = query.get("type", [None])[0]
            try:
                limit = self._parse_bounded_int(query.get("limit", ["50"])[0], name="limit", min_value=1, max_value=500)
                offset = self._parse_bounded_int(query.get("offset", ["0"])[0], name="offset", min_value=0, max_value=1000000)
            except ValueError as exc:
                self._inc_error()
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)}, request_id=request_id)
                return
            created_after = query.get("created_after", [None])[0]
            created_before = query.get("created_before", [None])[0]
            self._handle_reports_export(report_type=report_type, limit=limit, offset=offset, created_after=created_after, created_before=created_before)
            return

        if self._is_rate_limited():
            self._inc_error()
            self._send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"}, request_id=request_id)
            return

        if not self._is_authorized():
            self._inc_error()
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"}, request_id=request_id)
            return

        if parsed.path in {"/kpis", "/quality", "/hiring-funnel"}:
            query = parse_qs(parsed.query)
            csv_path = query.get("csv_path", [None])[0]
            as_of = query.get("as_of", [None])[0]
            self._handle_payload(parsed.path, csv_path, as_of, request_id)
            LOGGER.info("Request processed method=GET path=%s request_id=%s duration_ms=%.2f", parsed.path, request_id, (time.perf_counter() - start) * 1000)
            return

        self._inc_error()
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"}, request_id=request_id)

    def do_POST(self) -> None:  # noqa: N802
        self._inc_request()
        request_id = uuid.uuid4().hex
        start = time.perf_counter()
        parsed = urlparse(self.path)

        if parsed.path == "/reports/cleanup":
            if self._is_rate_limited():
                self._inc_error()
                self._send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"}, request_id=request_id)
                return

            if not self._is_authorized():
                self._inc_error()
                self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"}, request_id=request_id)
                return

            body = self._read_json_body(request_id)
            if body is None:
                return
            try:
                retention_days = self._parse_bounded_int(str(body.get("retention_days", self.config.default_retention_days)), name="retention_days", min_value=0, max_value=3650)
            except ValueError as exc:
                self._inc_error()
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)}, request_id=request_id)
                return
            self._handle_reports_cleanup(request_id=request_id, retention_days=retention_days)
            return

        if parsed.path not in {"/kpis", "/quality", "/hiring-funnel"}:
            self._inc_error()
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"}, request_id=request_id)
            return

        if self._is_rate_limited():
            self._inc_error()
            self._send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Rate limit exceeded"}, request_id=request_id)
            return

        if not self._is_authorized():
            self._inc_error()
            self._send_json(HTTPStatus.UNAUTHORIZED, {"error": "Unauthorized"}, request_id=request_id)
            return

        payload = self._read_json_body(request_id)
        if payload is None:
            return

        self._handle_payload(parsed.path, payload.get("csv_path"), payload.get("as_of"), request_id)
        LOGGER.info("Request processed method=POST path=%s request_id=%s duration_ms=%.2f", parsed.path, request_id, (time.perf_counter() - start) * 1000)


def run_server(host: str | None = None, port: int | None = None) -> None:
    config = AppConfig.from_env()
    selected_host = host or config.host
    selected_port = port or config.port

    logging.basicConfig(level=getattr(logging, config.log_level, logging.INFO), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    KPIHandler.config = config
    KPIHandler.store = ReportStore(config.db_path)
    KPIHandler.request_count = 0
    KPIHandler.error_count = 0
    KPIHandler._requests_by_ip = {}
    server = ThreadingHTTPServer((selected_host, selected_port), KPIHandler)
    LOGGER.info("Starting HR Insights server on %s:%s", selected_host, selected_port)
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HR Insights HTTP API server")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
