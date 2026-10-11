from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from netops_autopilot.ingestion.schemas import AlertInput, AlertRecord


class SQLiteAlertStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    event_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    device TEXT NOT NULL,
                    interface TEXT,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    message TEXT NOT NULL,
                    attributes_json TEXT NOT NULL,
                    received_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_device_received "
                "ON alerts(device, received_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_type_received "
                "ON alerts(event_type, received_at)"
            )
            connection.commit()

    def ping(self) -> bool:
        with self._connect() as connection:
            row = connection.execute("SELECT 1 AS ok").fetchone()
        return bool(row and row["ok"] == 1)

    def ingest(self, alert: AlertInput) -> tuple[AlertRecord, bool]:
        received_at = datetime.now(UTC)
        values = (
            alert.event_id,
            alert.source,
            alert.device,
            alert.interface,
            alert.event_type,
            alert.severity.value,
            alert.observed_at.isoformat(),
            alert.message,
            json.dumps(alert.attributes, sort_keys=True, separators=(",", ":")),
            received_at.isoformat(),
        )
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO alerts (
                    event_id, source, device, interface, event_type, severity,
                    observed_at, message, attributes_json, received_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            created = cursor.rowcount == 1
            connection.commit()
            row = connection.execute(
                "SELECT * FROM alerts WHERE event_id = ?", (alert.event_id,)
            ).fetchone()
        if row is None:  # pragma: no cover - defensive invariant
            raise RuntimeError("Stored alert could not be read back")
        return self._to_record(row), created

    def get(self, event_id: str) -> AlertRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM alerts WHERE event_id = ?", (event_id,)
            ).fetchone()
        return self._to_record(row) if row else None

    def list(
        self,
        *,
        device: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[AlertRecord]:
        clauses: list[str] = []
        parameters: list[str | int] = []
        if device:
            clauses.append("device = ?")
            parameters.append(device)
        if event_type:
            clauses.append("event_type = ?")
            parameters.append(event_type)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(limit)
        query = f"SELECT * FROM alerts{where} ORDER BY received_at DESC LIMIT ?"  # noqa: S608
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [self._to_record(row) for row in rows]

    def metrics(self) -> tuple[int, dict[str, int]]:
        with self._connect() as connection:
            total = connection.execute("SELECT COUNT(*) AS count FROM alerts").fetchone()
            groups = connection.execute(
                "SELECT severity, COUNT(*) AS count FROM alerts GROUP BY severity"
            ).fetchall()
        return int(total["count"]), {row["severity"]: int(row["count"]) for row in groups}

    @staticmethod
    def _to_record(row: sqlite3.Row) -> AlertRecord:
        return AlertRecord(
            event_id=row["event_id"],
            source=row["source"],
            device=row["device"],
            interface=row["interface"],
            event_type=row["event_type"],
            severity=row["severity"],
            observed_at=datetime.fromisoformat(row["observed_at"]),
            message=row["message"],
            attributes=json.loads(row["attributes_json"]),
            received_at=datetime.fromisoformat(row["received_at"]),
        )

