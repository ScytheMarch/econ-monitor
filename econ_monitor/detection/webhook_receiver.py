"""FastAPI webhook receiver for changedetection.io notifications.

Receives POST requests when monitored government pages change,
identifies which indicators map to the changed URL, and triggers
data refresh from FRED/OpenBB.
"""

from __future__ import annotations

import logging
try:
    import winsound  # Windows only
except ImportError:
    winsound = None  # type: ignore[assignment]
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from econ_monitor.config.indicators import INDICATORS, get_release_urls
from econ_monitor.config.settings import settings
from econ_monitor.data import cache
from econ_monitor.data.openbb_client import fetch_series

logger = logging.getLogger(__name__)

app = FastAPI(title="Econ Monitor Webhook Receiver")


@app.post("/webhook/change")
async def handle_change(request: Request) -> JSONResponse:
    """Handle a changedetection.io webhook notification.

    Expected payload (from changedetection apprise notification):
    {
        "url": "https://www.bls.gov/cpi/",
        "watch_uuid": "abc123",
        "title": "BLS CPI Page"
    }
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    url = body.get("url", "")
    title = body.get("title", "unknown")
    logger.info("Change detected: %s (%s)", title, url)

    # Map URL to indicator FRED IDs
    url_map = get_release_urls()
    matched_ids: list[str] = []

    for release_url, fred_ids in url_map.items():
        # Flexible matching: check if the detected URL contains or is contained in the release URL
        if url and (url in release_url or release_url in url):
            matched_ids.extend(fred_ids)

    if not matched_ids:
        logger.warning("No indicators matched for URL: %s", url)
        return JSONResponse({"status": "no_match", "url": url})

    # Refresh matched indicators
    results = []
    for sid in matched_ids:
        ind = INDICATORS.get(sid)
        if not ind:
            continue

        # Get current latest value before refresh
        old_date, old_value = cache.get_latest(sid)

        try:
            df = fetch_series(sid, lookback_years=1)
            if not df.empty:
                cache.upsert_observations(sid, df)
                cache.upsert_metadata(sid)

                # Check if we got a new data point
                new_date, new_value = cache.get_latest(sid)

                if new_date != old_date or new_value != old_value:
                    cache.log_activity(
                        series_id=sid,
                        category=ind.category,
                        event_type="new_release",
                        message=f"New data detected via page change: {title}",
                        old_value=old_value,
                        new_value=new_value,
                    )
                    results.append({
                        "series_id": sid,
                        "name": ind.name,
                        "status": "updated",
                        "old_value": old_value,
                        "new_value": new_value,
                    })

                    # Desktop notification sound
                    try:
                        winsound.Beep(1000, 200)
                    except Exception:
                        pass
                else:
                    results.append({"series_id": sid, "name": ind.name, "status": "no_change"})
        except Exception as e:
            logger.error("Failed to refresh %s: %s", sid, e)
            results.append({"series_id": sid, "name": ind.name, "status": "error", "error": str(e)})

    return JSONResponse({"status": "ok", "matched": len(matched_ids), "results": results})


@app.post("/webhook/poll")
async def handle_poll_update(request: Request) -> JSONResponse:
    """Handle an update notification from the FRED poller.

    Expected payload:
    {"series_id": "CPIAUCSL", "last_updated": "2026-03-14T08:30:00"}
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"status": "bad_request"}, status_code=400)

    series_id = body.get("series_id", "")
    if series_id not in INDICATORS:
        return JSONResponse({"status": "unknown_series"}, status_code=404)

    ind = INDICATORS[series_id]
    old_date, old_value = cache.get_latest(series_id)

    try:
        df = fetch_series(series_id, lookback_years=1)
        if not df.empty:
            cache.upsert_observations(series_id, df)
            cache.upsert_metadata(series_id, last_updated=body.get("last_updated", ""))

            new_date, new_value = cache.get_latest(series_id)
            if new_date != old_date or new_value != old_value:
                cache.log_activity(
                    series_id=series_id,
                    category=ind.category,
                    event_type="poll_update",
                    message=f"New data detected via FRED polling",
                    old_value=old_value,
                    new_value=new_value,
                )
                try:
                    winsound.Beep(800, 150)
                except Exception:
                    pass

        return JSONResponse({"status": "ok", "series_id": series_id})
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "indicators_tracked": len(INDICATORS),
    }
