import json
import logging
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DB_DIR = BASE_DIR / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = str(DB_DIR / "tickets.db")


def _get_conn() -> sqlite3.Connection:
    """Return a new connection with row_factory set for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
