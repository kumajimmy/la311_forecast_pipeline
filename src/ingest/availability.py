"""Check upstream data availability on the Socrata API."""

import logging
from datetime import date, datetime

import requests

from . import config

log = logging.getLogger(__name__)


def check_latest(year: int | None = None) -> tuple[date, bool]:
    """Query Socrata for the most recent createddate.

    Returns (latest_date, has_data).  When the API returns nothing or
    a network error occurs, returns (date.today(), False).
    """
    if year is None:
        year = date.today().year

    url = config.api_url(year)
    params: dict = {
        "$select": "max(createddate) as latest",
        "$limit": 1,
    }
    if config.APP_TOKEN:
        params["$$app_token"] = config.APP_TOKEN

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        rows = resp.json()
    except requests.RequestException:
        log.exception("Availability check failed for year=%d", year)
        return date.today(), False

    if not rows or not rows[0].get("latest"):
        # Current year may have no data yet; try previous year once.
        if year == date.today().year:
            log.info("No data for %d, trying %d", year, year - 1)
            return check_latest(year - 1)
        return date.today(), False

    latest_str: str = rows[0]["latest"]
    # Socrata returns ISO 8601 with optional millis, e.g. "2024-06-01T23:59:59.000"
    latest_dt = datetime.fromisoformat(latest_str.split(".")[0])
    latest_date = latest_dt.date()
    log.info("Latest available date: %s (year=%d)", latest_date, year)
    return latest_date, True
