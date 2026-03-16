"""Programmatic setup of changedetection.io watches via its REST API.

On first run, this module creates watches for all unique release URLs
in the indicator registry, configured to send webhook notifications
to our FastAPI receiver when page changes are detected.
"""

from __future__ import annotations

import logging
import time

import requests

from econ_monitor.config.indicators import INDICATORS, get_release_urls
from econ_monitor.config.settings import settings

logger = logging.getLogger(__name__)


def _api_url(path: str) -> str:
    base = settings.changedetection_url.rstrip("/")
    return f"{base}/api/v1{path}"


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if settings.changedetection_api_key:
        h["x-api-key"] = settings.changedetection_api_key
    return h


def is_running() -> bool:
    """Check if changedetection.io is reachable."""
    try:
        resp = requests.get(
            _api_url("/watch"),
            headers=_headers(),
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


def get_existing_watches() -> dict[str, str]:
    """Get all existing watches. Returns {url: uuid}."""
    try:
        resp = requests.get(_api_url("/watch"), headers=_headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # data is a dict of {uuid: {url: ..., ...}}
        return {info.get("url", ""): uuid for uuid, info in data.items()}
    except Exception as e:
        logger.error("Failed to get existing watches: %s", e)
        return {}


def create_watch(url: str, title: str, tag: str) -> str | None:
    """Create a new watch in changedetection.io.

    Returns the watch UUID or None on failure.
    """
    webhook_url = f"http://localhost:{settings.webhook_port}/webhook/change"

    payload = {
        "url": url,
        "title": title,
        "tag": tag,
        "notification_urls": [
            f"json://{webhook_url}",
        ],
        "notification_body": (
            '{{"url": "{{{{ url }}}}", '
            '"watch_uuid": "{{{{ watch_uuid }}}}", '
            '"title": "{{{{ watch_title }}}}"}}'
        ),
        "time_between_check": {"minutes": 15},
    }

    try:
        resp = requests.post(
            _api_url("/watch"),
            json=payload,
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        uuid = data.get("uuid")
        logger.info("Created watch for %s (uuid: %s)", url, uuid)
        return uuid
    except Exception as e:
        logger.error("Failed to create watch for %s: %s", url, e)
        return None


def setup_all_watches() -> dict[str, str]:
    """Create watches for all unique release URLs not already monitored.

    Returns {url: uuid} for all watches (existing + new).
    """
    if not is_running():
        logger.warning("changedetection.io is not running at %s", settings.changedetection_url)
        return {}

    existing = get_existing_watches()
    url_map = get_release_urls()
    all_watches = dict(existing)

    for url, fred_ids in url_map.items():
        if url in existing:
            logger.debug("Watch already exists for %s", url)
            continue

        # Build a title from the indicator names
        names = [INDICATORS[sid].name for sid in fred_ids if sid in INDICATORS]
        title = ", ".join(names[:3])
        if len(names) > 3:
            title += f" (+{len(names) - 3} more)"

        # Tag by category
        categories = set(INDICATORS[sid].category for sid in fred_ids if sid in INDICATORS)
        tag = ", ".join(sorted(categories))

        uuid = create_watch(url, title, tag)
        if uuid:
            all_watches[url] = uuid

        # Rate limit: don't hammer the API
        time.sleep(0.5)

    logger.info("Total watches: %d (new: %d)", len(all_watches), len(all_watches) - len(existing))
    return all_watches


def remove_all_watches() -> int:
    """Remove all watches. Returns count removed."""
    existing = get_existing_watches()
    removed = 0
    for url, uuid in existing.items():
        try:
            resp = requests.delete(
                _api_url(f"/watch/{uuid}"),
                headers=_headers(),
                timeout=10,
            )
            if resp.status_code == 204:
                removed += 1
        except Exception as e:
            logger.error("Failed to remove watch %s: %s", uuid, e)
    return removed
