"""Configuration for LA 311 ingestion, driven by environment variables."""

import os

# Per-year Socrata resource IDs for MyLA311 Service Request Data
RESOURCE_IDS: dict[int, str] = {
    2025: "h73f-gn57",
    2024: "b7dx-7gc3",
    2023: "4a4x-mna2",
    2022: "i5ke-k6by",
    2021: "97z7-y5bt",
    2020: "rq3b-xjk8",
}

API_HOST = os.environ.get("LA311_API_HOST", "https://data.lacity.org")
APP_TOKEN = os.environ.get("LA311_APP_TOKEN", "")
RAW_DIR = os.environ.get("LA311_RAW_DIR", "data/raw")
PAGE_SIZE = int(os.environ.get("LA311_PAGE_SIZE", "5000"))


def api_url(year: int) -> str:
    """Return the Socrata JSON endpoint for a given year."""
    rid = RESOURCE_IDS.get(year)
    if not rid:
        raise ValueError(f"No known resource ID for year {year}. Known: {sorted(RESOURCE_IDS)}")
    return f"{API_HOST}/resource/{rid}.json"
