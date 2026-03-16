"""Track actual vs consensus/expected values for economic surprises.

Consensus values are stored in a JSON file that the user can update
before releases. Future enhancement: scrape from public calendars.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from econ_monitor.config.settings import settings

logger = logging.getLogger(__name__)

_CONSENSUS_FILE = settings.project_root / "data" / "consensus.json"


def _load_consensus() -> dict:
    """Load consensus expectations from JSON file.

    Format: {"CPIAUCSL": {"2026-02": {"expected": 0.3, "source": "manual"}}, ...}
    """
    if not _CONSENSUS_FILE.exists():
        return {}
    try:
        return json.loads(_CONSENSUS_FILE.read_text())
    except Exception as e:
        logger.warning("Failed to load consensus file: %s", e)
        return {}


def get_consensus(series_id: str, period: str) -> float | None:
    """Get consensus expectation for a series and period (e.g., '2026-02')."""
    data = _load_consensus()
    entry = data.get(series_id, {}).get(period, {})
    return entry.get("expected")


def compute_surprise(actual: float, expected: float | None) -> dict | None:
    """Compute the surprise: actual - expected and standardized surprise.

    Returns None if expected is not available.
    """
    if expected is None:
        return None

    diff = actual - expected
    pct_surprise = (diff / abs(expected) * 100) if expected != 0 else 0.0

    if abs(pct_surprise) < 5:
        label = "In-line"
        color = "#6b7280"
    elif pct_surprise > 0:
        label = "Beat"
        color = "#22c55e"
    else:
        label = "Miss"
        color = "#ef4444"

    return {
        "actual": actual,
        "expected": expected,
        "diff": round(diff, 4),
        "pct_surprise": round(pct_surprise, 2),
        "label": label,
        "color": color,
    }


def save_consensus(series_id: str, period: str, expected: float, source: str = "manual") -> None:
    """Save a consensus expectation."""
    data = _load_consensus()
    data.setdefault(series_id, {})[period] = {
        "expected": expected,
        "source": source,
    }
    _CONSENSUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CONSENSUS_FILE.write_text(json.dumps(data, indent=2))
