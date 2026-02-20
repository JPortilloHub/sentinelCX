"""SQLite persistence for dashboard events and metrics."""

import json
import sqlite3
import time
from pathlib import Path

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "dashboard.db"


class DashboardStore:
    """Lightweight SQLite store for dashboard history."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = str(db_path or _DEFAULT_DB_PATH)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                data TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS tickets (
                conversation_id TEXT PRIMARY KEY,
                decision TEXT,
                category TEXT,
                priority TEXT,
                confidence REAL,
                cost_usd REAL DEFAULT 0,
                duration_ms REAL DEFAULT 0,
                turns INTEGER DEFAULT 0,
                success INTEGER DEFAULT 0,
                created_at REAL NOT NULL,
                completed_at REAL
            );

            CREATE INDEX IF NOT EXISTS idx_events_cid ON events(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
            CREATE INDEX IF NOT EXISTS idx_events_ts ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_tickets_decision ON tickets(decision);
            CREATE INDEX IF NOT EXISTS idx_tickets_created ON tickets(created_at);
        """)
        self._conn.commit()

    def save_event(
        self, event_type: str, conversation_id: str, timestamp: float, data: dict
    ) -> None:
        self._conn.execute(
            "INSERT INTO events (type, conversation_id, timestamp, data) VALUES (?, ?, ?, ?)",
            (event_type, conversation_id, timestamp, json.dumps(data)),
        )
        self._conn.commit()

    def save_ticket(self, conversation_id: str, data: dict) -> None:
        """Upsert a ticket record on completion."""
        self._conn.execute(
            """
            INSERT INTO tickets
                (conversation_id, decision, category, priority, confidence,
                 cost_usd, duration_ms, turns, success, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(conversation_id) DO UPDATE SET
                decision=excluded.decision,
                category=excluded.category,
                priority=excluded.priority,
                confidence=excluded.confidence,
                cost_usd=excluded.cost_usd,
                duration_ms=excluded.duration_ms,
                turns=excluded.turns,
                success=excluded.success,
                completed_at=excluded.completed_at
        """,
            (
                conversation_id,
                data.get("decision", ""),
                data.get("category", ""),
                data.get("priority", ""),
                data.get("confidence"),
                data.get("cost_usd", 0),
                data.get("duration_ms", 0),
                data.get("turns", 0),
                1 if data.get("success") else 0,
                data.get("created_at", time.time()),
                time.time(),
            ),
        )
        self._conn.commit()

    def get_metrics(self) -> dict:
        """Compute aggregate metrics from all stored tickets."""
        row = self._conn.execute(
            """
            SELECT
                COUNT(*) as total_processed,
                COALESCE(
                    SUM(CASE WHEN decision='auto_handle' THEN 1 ELSE 0 END), 0
                ) as auto_handle_count,
                COALESCE(
                    SUM(CASE WHEN decision='needs_research' THEN 1 ELSE 0 END), 0
                ) as needs_research_count,
                COALESCE(
                    SUM(CASE WHEN decision='escalate' THEN 1 ELSE 0 END), 0
                ) as escalate_count,
                COALESCE(SUM(cost_usd), 0) as total_cost_usd,
                COALESCE(SUM(duration_ms), 0) as total_duration_ms,
                COALESCE(SUM(confidence), 0) as confidence_sum,
                COALESCE(
                    SUM(CASE WHEN confidence IS NOT NULL THEN 1 ELSE 0 END), 0
                ) as confidence_count
            FROM tickets
            """
        ).fetchone()

        category_rows = self._conn.execute(
            "SELECT category, COUNT(*) as cnt FROM tickets WHERE category != '' GROUP BY category"
        ).fetchall()

        return {
            "total_processed": row["total_processed"],
            "auto_handle_count": row["auto_handle_count"],
            "needs_research_count": row["needs_research_count"],
            "escalate_count": row["escalate_count"],
            "total_cost_usd": row["total_cost_usd"],
            "total_duration_ms": row["total_duration_ms"],
            "confidence_sum": row["confidence_sum"],
            "confidence_count": row["confidence_count"],
            "category_counts": {r["category"]: r["cnt"] for r in category_rows},
        }

    def get_recent_events(self, limit: int = 100) -> list[dict]:
        """Get the most recent events."""
        rows = self._conn.execute(
            "SELECT type, conversation_id, timestamp, data FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "type": r["type"],
                "conversation_id": r["conversation_id"],
                "timestamp": r["timestamp"],
                "data": json.loads(r["data"]),
            }
            for r in reversed(rows)  # return in chronological order
        ]

    def get_tickets(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """Get completed tickets, newest first."""
        rows = self._conn.execute(
            "SELECT * FROM tickets ORDER BY completed_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_ticket_events(self, conversation_id: str) -> list[dict]:
        """Get all events for a specific ticket."""
        rows = self._conn.execute(
            "SELECT type, conversation_id, timestamp, data "
            "FROM events WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
        return [
            {
                "type": r["type"],
                "conversation_id": r["conversation_id"],
                "timestamp": r["timestamp"],
                "data": json.loads(r["data"]),
            }
            for r in rows
        ]

    def close(self) -> None:
        self._conn.close()
