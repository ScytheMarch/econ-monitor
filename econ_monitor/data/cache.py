"""SQLite storage layer for economic indicator data.

Three tables:
  - observations: time series data (series_id, date, value)
  - series_metadata: last_updated, last_fetched, title, etc.
  - activity_feed: log of data changes for the dashboard feed
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import pandas as pd

from econ_monitor.config.settings import settings


def _db_path() -> Path:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    return settings.db_path


@contextmanager
def _connect() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(str(_db_path()), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS observations (
                series_id TEXT NOT NULL,
                date      TEXT NOT NULL,
                value     REAL,
                PRIMARY KEY (series_id, date)
            );

            CREATE TABLE IF NOT EXISTS series_metadata (
                series_id    TEXT PRIMARY KEY,
                title        TEXT,
                frequency    TEXT,
                units        TEXT,
                last_updated TEXT,
                last_fetched TEXT
            );

            CREATE TABLE IF NOT EXISTS activity_feed (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT NOT NULL,
                series_id  TEXT NOT NULL,
                category   TEXT,
                event_type TEXT,
                old_value  REAL,
                new_value  REAL,
                message    TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_obs_series ON observations(series_id);
            CREATE INDEX IF NOT EXISTS idx_feed_ts ON activity_feed(timestamp DESC);
        """)


# ---------------------------------------------------------------------------
# Observations
# ---------------------------------------------------------------------------

def upsert_observations(series_id: str, df: pd.DataFrame) -> int:
    """Write observations to the database. df must have a DatetimeIndex and a 'value' column.

    Returns the number of rows upserted.
    """
    if df.empty:
        return 0

    rows = [
        (series_id, idx.strftime("%Y-%m-%d"), float(row["value"]))
        for idx, row in df.iterrows()
        if pd.notna(row["value"])
    ]
    with _connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO observations (series_id, date, value) VALUES (?, ?, ?)",
            rows,
        )
    return len(rows)


def get_observations(series_id: str, start_date: str | None = None) -> pd.DataFrame:
    """Read observations for a series. Returns DataFrame with DatetimeIndex and 'value' column."""
    query = "SELECT date, value FROM observations WHERE series_id = ?"
    params: list = [series_id]
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    query += " ORDER BY date"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    if not rows:
        return pd.DataFrame(columns=["value"])

    df = pd.DataFrame(rows, columns=["date", "value"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    return df


def get_latest(series_id: str) -> tuple[str | None, float | None]:
    """Return (date_str, value) for the most recent observation, or (None, None)."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT date, value FROM observations WHERE series_id = ? ORDER BY date DESC LIMIT 1",
            (series_id,),
        ).fetchone()
    if row:
        return row["date"], row["value"]
    return None, None


def get_previous(series_id: str) -> tuple[str | None, float | None]:
    """Return the second-most-recent observation."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT date, value FROM observations WHERE series_id = ? ORDER BY date DESC LIMIT 1 OFFSET 1",
            (series_id,),
        ).fetchone()
    if row:
        return row["date"], row["value"]
    return None, None


# ---------------------------------------------------------------------------
# Series metadata
# ---------------------------------------------------------------------------

def upsert_metadata(
    series_id: str,
    title: str = "",
    frequency: str = "",
    units: str = "",
    last_updated: str = "",
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """INSERT INTO series_metadata (series_id, title, frequency, units, last_updated, last_fetched)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(series_id) DO UPDATE SET
                   title = COALESCE(NULLIF(excluded.title, ''), series_metadata.title),
                   frequency = COALESCE(NULLIF(excluded.frequency, ''), series_metadata.frequency),
                   units = COALESCE(NULLIF(excluded.units, ''), series_metadata.units),
                   last_updated = COALESCE(NULLIF(excluded.last_updated, ''), series_metadata.last_updated),
                   last_fetched = excluded.last_fetched
            """,
            (series_id, title, frequency, units, last_updated, now),
        )


def get_metadata(series_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM series_metadata WHERE series_id = ?", (series_id,)
        ).fetchone()
    return dict(row) if row else None


def get_all_metadata() -> list[dict]:
    """Return metadata rows for all series."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM series_metadata").fetchall()
    return [dict(r) for r in rows]


def is_stale(series_id: str, max_age_hours: int = 24) -> bool:
    """Return True if series hasn't been fetched within max_age_hours."""
    meta = get_metadata(series_id)
    if not meta or not meta.get("last_fetched"):
        return True
    last = datetime.fromisoformat(meta["last_fetched"])
    age = datetime.now(timezone.utc) - last
    return age.total_seconds() > max_age_hours * 3600


# ---------------------------------------------------------------------------
# Activity feed
# ---------------------------------------------------------------------------

def log_activity(
    series_id: str,
    category: str,
    event_type: str,
    message: str,
    old_value: float | None = None,
    new_value: float | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """INSERT INTO activity_feed (timestamp, series_id, category, event_type, old_value, new_value, message)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (now, series_id, category, event_type, old_value, new_value, message),
        )


def get_activity_feed(limit: int = 50) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM activity_feed ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# Initialize on import
init_db()
