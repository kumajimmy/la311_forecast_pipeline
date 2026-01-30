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
    """
    Return a Socrata API endpoint URL.

    Priority:
    1) LA311_API_BASE env var (can be full URL or a resource id like 'ndkd-k878')
    2) Year-specific RESOURCE_IDS mapping
    3) Fallback to the continuously-updated dataset
    """
    env = os.getenv("LA311_API_BASE")
    if env:
        # allow either full URL or just a dataset/resource id
        if env.startswith("http://") or env.startswith("https://"):
            return env
        return f"https://data.lacity.org/resource/{env}.json"

    rid = RESOURCE_IDS.get(year)
    if rid:
        return f"https://data.lacity.org/resource/{rid}.json"

    # fallback: don't crash on new years
    return "https://data.lacity.org/resource/ndkd-k878.json"
