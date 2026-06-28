"""SQLite database initialisation, ticket persistence, and retrieval."""

import json
import logging
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = str(BASE_DIR / "data" / "tickets.db")


def _get_conn() -> sqlite3.Connection:
    """Return a new connection with row_factory set for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the tickets table if it does not exist yet."""
    conn = _get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id           TEXT PRIMARY KEY,
            text         TEXT,
            sentiment_score INTEGER,
            urgency_score   INTEGER,
            churn_risk   BOOLEAN,
            tone         TEXT,
            reason       TEXT,
            key_phrases  TEXT,
            flagged      BOOLEAN,
            alert_reason TEXT,
            source       TEXT,
            created_at   TEXT
        )
        """
    )
    try:
        conn.execute("ALTER TABLE tickets ADD COLUMN draft_reply TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()
    logger.info("Database initialised (table: tickets)")


def save_ticket(
    ticket_id: str,
    text: str,
    scores: dict,
    flagged: bool,
    alert_reason: str,
    source: str,
    draft_reply: str | None = None,
) -> None:
    """INSERT OR REPLACE a ticket record with classifier scores.

    key_phrases is stored as a JSON-encoded string.
    """
    conn = _get_conn()
    conn.execute(
        """
        INSERT OR REPLACE INTO tickets
            (id, text, sentiment_score, urgency_score, churn_risk,
             tone, reason, key_phrases, flagged, alert_reason, source,
             created_at, draft_reply)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            text,
            scores.get("sentiment_score"),
            scores.get("urgency_score"),
            scores.get("churn_risk"),
            scores.get("tone"),
            scores.get("reason"),
            json.dumps(scores.get("key_phrases", [])),
            flagged,
            alert_reason,
            source,
            datetime.now(timezone.utc).isoformat(),
            draft_reply,
        ),
    )
    conn.commit()
    conn.close()
    logger.info("Saved ticket %s (flagged=%s)", ticket_id, flagged)


def get_all_tickets(flagged_only: bool = False) -> list[dict]:
    """Retrieve all tickets, optionally filtering to flagged-only.

    key_phrases is parsed back from its JSON string representation.
    """
    conn = _get_conn()
    if flagged_only:
        rows = conn.execute(
            "SELECT * FROM tickets WHERE flagged = 1 ORDER BY created_at DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC"
        ).fetchall()
    conn.close()

    results: list[dict] = []
    for row in rows:
        d = dict(row)
        # Parse the JSON-encoded key_phrases back into a list
        try:
            d["key_phrases"] = json.loads(d.get("key_phrases", "[]"))
        except (json.JSONDecodeError, TypeError):
            d["key_phrases"] = []
        results.append(d)

    return results


def get_ticket_by_id(ticket_id: str) -> dict | None:
    """Retrieve a single ticket by its ID, or None if not found."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    try:
        d["key_phrases"] = json.loads(d.get("key_phrases", "[]"))
    except (json.JSONDecodeError, TypeError):
        d["key_phrases"] = []
    return d


def delete_ticket(ticket_id: str) -> bool:
    """Delete a ticket by ID. Returns True if a row was actually removed."""
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    removed = cursor.rowcount > 0
    conn.close()
    if removed:
        logger.info("Deleted ticket %s", ticket_id)
    return removed


def delete_all_tickets() -> int:
    """Delete all tickets. Returns the number of rows removed."""
    conn = _get_conn()
    cursor = conn.execute("DELETE FROM tickets")
    conn.commit()
    removed = cursor.rowcount
    conn.close()
    if removed > 0:
        logger.info("Deleted all %d tickets", removed)
    return removed


def get_stats() -> dict:
    """Return aggregated statistics across all tickets."""
    conn = _get_conn()

    row = conn.execute(
        """
        SELECT
            COUNT(*)                          AS total_tickets,
            COALESCE(SUM(flagged), 0)         AS flagged_tickets,
            COALESCE(AVG(sentiment_score), 0) AS avg_sentiment,
            COALESCE(AVG(urgency_score), 0)   AS avg_urgency,
            COALESCE(SUM(churn_risk), 0)      AS churn_risk_count
        FROM tickets
        """
    ).fetchone()

    stats = dict(row) if row else {
        "total_tickets": 0,
        "flagged_tickets": 0,
        "avg_sentiment": 0,
        "avg_urgency": 0,
        "churn_risk_count": 0,
    }

    # Round averages for clean display
    stats["avg_sentiment"] = round(stats["avg_sentiment"], 1)
    stats["avg_urgency"] = round(stats["avg_urgency"], 1)

    # Tone distribution
    tone_rows = conn.execute(
        "SELECT tone, COUNT(*) as count FROM tickets WHERE tone IS NOT NULL GROUP BY tone"
    ).fetchall()
    stats["tone_distribution"] = {r["tone"]: r["count"] for r in tone_rows}

    conn.close()
    return stats
