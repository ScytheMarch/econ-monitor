"""Background FRED poller using APScheduler.

Periodically checks FRED API for updated series and triggers data refresh.
This is a fallback/complement to changedetection.io monitoring.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

import requests

from econ_monitor.config.indicators import INDICATORS
from econ_monitor.config.settings import settings
from econ_monitor.data import cache
from econ_monitor.data.openbb_client import fetch_series, check_series_updated

logger = logging.getLogger(__name__)


def poll_all_series() -> None:
    """Check all tracked series for updates and refresh if new data is available."""
    logger.info("Starting FRED poll cycle at %s", datetime.now(timezone.utc).isoformat())

    updated_count = 0
    for sid, ind in INDICATORS.items():
        try:
            # Check if FRED reports a newer update than what we have cached
            fred_updated = check_series_updated(sid)
            if fred_updated is None:
                continue

            meta = cache.get_metadata(sid)
            cached_updated = meta.get("last_updated", "") if meta else ""

            if fred_updated != cached_updated:
                logger.info("Update detected for %s (%s): %s -> %s",
                           ind.name, sid, cached_updated, fred_updated)

                # Get old value before refresh
                old_date, old_value = cache.get_latest(sid)

                # Fetch new data
                df = fetch_series(sid, lookback_years=1)
                if not df.empty:
                    cache.upsert_observations(sid, df)
                    cache.upsert_metadata(sid, last_updated=fred_updated)

                    new_date, new_value = cache.get_latest(sid)
                    if new_date != old_date or new_value != old_value:
                        cache.log_activity(
                            series_id=sid,
                            category=ind.category,
                            event_type="poll_update",
                            message=f"New data detected via FRED polling",
                            old_value=old_value,
                            new_value=new_value,
                        )
                        updated_count += 1

                        # Notify webhook receiver (optional, for logging)
                        try:
                            requests.post(
                                f"http://localhost:{settings.webhook_port}/webhook/poll",
                                json={"series_id": sid, "last_updated": fred_updated},
                                timeout=5,
                            )
                        except Exception:
                            pass  # Webhook receiver may not be running
            else:
                # No update, but still refresh metadata timestamp
                cache.upsert_metadata(sid)

        except Exception as e:
            logger.error("Error polling %s: %s", sid, e)

    logger.info("Poll cycle complete. %d series updated.", updated_count)


def run_poller() -> None:
    """Run the poller as a long-lived background process with APScheduler."""
    from apscheduler.schedulers.blocking import BlockingScheduler

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [POLLER] %(levelname)s %(message)s",
    )

    scheduler = BlockingScheduler()
    scheduler.add_job(
        poll_all_series,
        "interval",
        minutes=settings.poll_interval_minutes,
        id="fred_poll",
        max_instances=1,
        next_run_time=datetime.now(timezone.utc),  # Run immediately on start
    )

    logger.info("FRED poller started. Interval: %d minutes", settings.poll_interval_minutes)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("FRED poller stopped.")
        scheduler.shutdown()


if __name__ == "__main__":
    run_poller()
