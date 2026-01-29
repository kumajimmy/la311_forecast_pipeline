"""HTTP client for the LA 311 Socrata API."""

import logging
from datetime import date, timedelta

import requests

from . import config

log = logging.getLogger(__name__)


def fetch_day(day: date, limit: int | None = None) -> list[dict]:
    """Fetch all 311 requests created on *day*. Returns list of dicts."""
    url = config.api_url(day.year)
    next_day = day + timedelta(days=1)
    where = (
        f"createddate >= '{day.isoformat()}T00:00:00' "
        f"AND createddate < '{next_day.isoformat()}T00:00:00'"
    )
    params: dict = {
        "$where": where,
        "$order": "createddate ASC",
        "$limit": config.PAGE_SIZE,
    }
    if config.APP_TOKEN:
        params["$$app_token"] = config.APP_TOKEN

    all_rows: list[dict] = []
    offset = 0

    while True:
        params["$offset"] = offset
        log.info("Fetching offset=%d for %s", offset, day)
        resp = requests.get(url, params=params, timeout=120)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            break
        all_rows.extend(rows)
        if limit and len(all_rows) >= limit:
            all_rows = all_rows[:limit]
            break
        offset += config.PAGE_SIZE

    log.info("Fetched %d records for %s", len(all_rows), day)
    return all_rows
