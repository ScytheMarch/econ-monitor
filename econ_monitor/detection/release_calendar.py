"""Economic release calendar using FRED releases API.

Provides upcoming and recent release dates for tracked indicators.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import requests

from econ_monitor.config.settings import settings

logger = logging.getLogger(__name__)

_FRED_BASE = "https://api.stlouisfed.org/fred"


def get_upcoming_releases(days_ahead: int = 14) -> list[dict]:
    """Fetch upcoming economic releases from FRED within the next N days.

    Returns list of {name, date, release_id, link}.
    """
    if not settings.fred_api_key:
        return []

    try:
        now = datetime.now()
        end = now + timedelta(days=days_ahead)

        resp = requests.get(
            f"{_FRED_BASE}/releases/dates",
            params={
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "include_release_dates_with_no_data": "false",
                "realtime_start": now.strftime("%Y-%m-%d"),
                "realtime_end": end.strftime("%Y-%m-%d"),
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        releases = []
        for item in data.get("release_dates", []):
            releases.append({
                "release_id": item.get("release_id"),
                "name": item.get("release_name", "Unknown"),
                "date": item.get("date", ""),
            })

        return sorted(releases, key=lambda r: r["date"])

    except Exception as e:
        logger.error("Failed to fetch release calendar: %s", e)
        return []


def get_recent_releases(days_back: int = 7) -> list[dict]:
    """Fetch recent economic releases from the past N days."""
    if not settings.fred_api_key:
        return []

    try:
        now = datetime.now()
        start = now - timedelta(days=days_back)

        resp = requests.get(
            f"{_FRED_BASE}/releases/dates",
            params={
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "include_release_dates_with_no_data": "false",
                "realtime_start": start.strftime("%Y-%m-%d"),
                "realtime_end": now.strftime("%Y-%m-%d"),
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        releases = []
        for item in data.get("release_dates", []):
            releases.append({
                "release_id": item.get("release_id"),
                "name": item.get("release_name", "Unknown"),
                "date": item.get("date", ""),
            })

        return sorted(releases, key=lambda r: r["date"], reverse=True)

    except Exception as e:
        logger.error("Failed to fetch recent releases: %s", e)
        return []
