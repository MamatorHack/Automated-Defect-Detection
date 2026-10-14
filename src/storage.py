from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


ReviewAction = Literal["ACCEPT", "REJECT", "ESCALATE"]


class InspectionStore:
    """SQLite metadata store. Raw inspection images are intentionally not persisted."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS inspections (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    category TEXT NOT NULL,
                    engine TEXT NOT NULL,
                    model_artifact_sha256 TEXT,
                    filename TEXT NOT NULL,
                    file_sha256 TEXT NOT NULL,
                    model_decision TEXT NOT NULL,
                    anomaly_score REAL NOT NULL,
                    threshold REAL NOT NULL,
                    latency_ms REAL NOT NULL,
                    operator_decision TEXT,
                    reviewed_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_inspections_created_at
                ON inspections(created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_inspections_category
                ON inspections(category);
                """
            )

    def record(
        self,
        *,
        category: str,
        engine: str,
        model_artifact_sha256: str | None,
        filename: str,
        file_sha256: str,
        model_decision: str,
        anomaly_score: float,
        threshold: float,
        latency_ms: float,
    ) -> str:
        inspection_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO inspections (
                    id, created_at, category, engine, model_artifact_sha256,
                    filename, file_sha256, model_decision, anomaly_score,
                    threshold, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inspection_id,
                    created_at,
                    category,
                    engine,
                    model_artifact_sha256,
                    filename,
                    file_sha256,
                    model_decision,
                    float(anomaly_score),
                    float(threshold),
                    float(latency_ms),
                ),
            )
        return inspection_id

    def review(self, inspection_id: str, action: ReviewAction) -> dict | None:
        reviewed_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            cursor = db.execute(
                """
                UPDATE inspections
                SET operator_decision = ?, reviewed_at = ?
                WHERE id = ?
                """,
                (action, reviewed_at, inspection_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get(inspection_id)

    def get(self, inspection_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM inspections WHERE id = ?", (inspection_id,)).fetchone()
        return dict(row) if row else None

    def recent(self, limit: int = 20) -> list[dict]:
        limit = max(1, min(int(limit), 200))
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM inspections ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> dict:
        with self._connect() as db:
            total = db.execute("SELECT COUNT(*) FROM inspections").fetchone()[0]
            anomalies = db.execute(
                "SELECT COUNT(*) FROM inspections WHERE model_decision = 'ANOMALY'"
            ).fetchone()[0]
            reviewed = db.execute(
                "SELECT COUNT(*) FROM inspections WHERE operator_decision IS NOT NULL"
            ).fetchone()[0]
            avg_latency = db.execute("SELECT AVG(latency_ms) FROM inspections").fetchone()[0]
        return {
            "total_inspections": int(total),
            "model_anomalies": int(anomalies),
            "reviewed_by_operator": int(reviewed),
            "average_latency_ms": round(float(avg_latency), 2) if avg_latency is not None else None,
        }
