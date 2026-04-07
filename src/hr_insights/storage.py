from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class ReportRecord:
    id: int
    created_at: str
    report_type: str
    csv_path: str
    as_of: str | None
    payload: dict


class ReportStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS report_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    csv_path TEXT NOT NULL,
                    as_of TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_report(self, report_type: str, csv_path: str, as_of: str | None, payload: dict) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO report_runs (created_at, report_type, csv_path, as_of, payload_json) VALUES (?, ?, ?, ?, ?)",
                (created_at, report_type, csv_path, as_of, json.dumps(payload, sort_keys=True)),
            )
            conn.commit()

    def list_reports(
        self,
        report_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
        created_after: str | None = None,
        created_before: str | None = None,
    ) -> list[ReportRecord]:
        query = "SELECT id, created_at, report_type, csv_path, as_of, payload_json FROM report_runs WHERE 1=1"
        params: list = []
        if report_type:
            query += " AND report_type = ?"
            params.append(report_type)
        if created_after:
            query += " AND created_at >= ?"
            params.append(created_after)
        if created_before:
            query += " AND created_at <= ?"
            params.append(created_before)
        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        return [
            ReportRecord(
                id=row[0],
                created_at=row[1],
                report_type=row[2],
                csv_path=row[3],
                as_of=row[4],
                payload=json.loads(row[5]),
            )
            for row in rows
        ]

    def list_reports_csv(
        self,
        report_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
        created_after: str | None = None,
        created_before: str | None = None,
    ) -> str:
        rows = self.list_reports(
            report_type=report_type,
            limit=limit,
            offset=offset,
            created_after=created_after,
            created_before=created_before,
        )
        lines = ["id,created_at,report_type,csv_path,as_of,payload_json"]
        for row in rows:
            payload = json.dumps(row.payload, sort_keys=True).replace('"', '""')
            safe_csv_path = row.csv_path.replace('"', '""')
            safe_as_of = (row.as_of or "").replace('"', '""')
            lines.append(f'"{row.id}","{row.created_at}","{row.report_type}","{safe_csv_path}","{safe_as_of}","{payload}"')
        return "\n".join(lines) + "\n"

    def cleanup_old_reports(self, retention_days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        cutoff_iso = cutoff.isoformat()
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM report_runs WHERE created_at < ?", (cutoff_iso,))
            conn.commit()
            return cur.rowcount
