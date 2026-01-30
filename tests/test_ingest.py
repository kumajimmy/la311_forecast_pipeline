"""Unit tests for the ingestion module."""

import gzip
import json
from datetime import date
from pathlib import Path
from unittest import mock

import pytest
import requests as requests_mod

from src.ingest import availability, config, writer
from src.ingest.cli import parse_args, resolve_dates


# --- config ---

def test_config_has_resource_ids():
    assert 2024 in config.RESOURCE_IDS
    assert config.PAGE_SIZE == 5000


def test_api_url(monkeypatch):
    # Ensure env var override doesn't affect this test
    monkeypatch.delenv("LA311_API_BASE", raising=False)
    url = config.api_url(2024)
    assert "b7dx-7gc3" in url


def test_api_url_unknown_year(monkeypatch):
    # Ensure env var override doesn't affect this test
    monkeypatch.delenv("LA311_API_BASE", raising=False)
    url = config.api_url(2099)
    assert "ndkd-k878" in url


# --- writer ---

def test_partition_path():
    with mock.patch.object(config, "RAW_DIR", "data/raw"):
        p = writer.partition_path(date(2024, 1, 15))
        assert p == Path("data/raw/date=2024-01-15/la311_20240115.jsonl.gz")


def test_write_day(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RAW_DIR", str(tmp_path))
    records = [{"id": "1", "type": "Graffiti"}, {"id": "2", "type": "Bulky Items"}]
    out = writer.write_day(date(2024, 3, 1), records)
    assert out.exists()
    with gzip.open(out, "rt") as f:
        lines = f.readlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["id"] == "1"


def test_write_day_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RAW_DIR", str(tmp_path))
    day = date(2024, 3, 1)
    writer.write_day(day, [{"a": 1}])
    writer.write_day(day, [{"a": 2}])  # overwrite
    with gzip.open(writer.partition_path(day), "rt") as f:
        rec = json.loads(f.readline())
    assert rec["a"] == 2


def test_api_url_env_override(monkeypatch):
    monkeypatch.setenv("LA311_API_BASE", "https://example.com/foo.json")
    url = config.api_url(2024)
    assert url == "https://example.com/foo.json"


def test_api_url_env_override_resource_id(monkeypatch):
    monkeypatch.setenv("LA311_API_BASE", "ndkd-k878")
    url = config.api_url(2024)
    assert url.endswith("/ndkd-k878.json")


# --- availability ---

def test_check_latest_success(monkeypatch):
    """check_latest returns parsed date when API has data."""
    mock_resp = mock.Mock()
    mock_resp.json.return_value = [{"latest": "2026-01-28T23:45:00.000"}]
    mock_resp.raise_for_status = mock.Mock()

    monkeypatch.setattr("src.ingest.availability.requests.get", lambda *a, **kw: mock_resp)
    monkeypatch.delenv("LA311_API_BASE", raising=False)

    d, ok = availability.check_latest(2026)
    assert d == date(2026, 1, 28)
    assert ok is True


def test_check_latest_empty(monkeypatch):
    """check_latest returns (today, False) when API returns no data for non-current year."""
    mock_resp = mock.Mock()
    mock_resp.json.return_value = [{"latest": None}]
    mock_resp.raise_for_status = mock.Mock()

    monkeypatch.setattr("src.ingest.availability.requests.get", lambda *a, **kw: mock_resp)
    monkeypatch.delenv("LA311_API_BASE", raising=False)

    d, ok = availability.check_latest(2099)  # non-current year to skip fallback
    assert ok is False


def test_check_latest_network_error(monkeypatch):
    """check_latest returns (today, False) on network failure."""
    def boom(*a, **kw):
        raise requests_mod.exceptions.ConnectionError("fail")

    monkeypatch.setattr("src.ingest.availability.requests.get", boom)
    monkeypatch.delenv("LA311_API_BASE", raising=False)

    d, ok = availability.check_latest(2099)
    assert ok is False


# --- cli ---

def test_parse_args_date():
    args = parse_args(["--date", "2024-06-01"])
    assert args.date == date(2024, 6, 1)


def test_parse_args_range():
    args = parse_args(["--start", "2024-01-01", "--end", "2024-01-03"])
    assert args.start == date(2024, 1, 1)
    assert args.end == date(2024, 1, 3)


def test_resolve_dates_range():
    args = parse_args(["--start", "2024-01-01", "--end", "2024-01-03"])
    dates = resolve_dates(args)
    assert len(dates) == 3


def test_resolve_dates_default():
    args = parse_args([])
    dates = resolve_dates(args)
    assert len(dates) == 1  # yesterday


# --- cli: --latest ---

def test_resolve_dates_latest(monkeypatch):
    """--latest resolves to the date returned by check_latest."""
    monkeypatch.setattr(
        "src.ingest.cli.availability.check_latest",
        lambda year=None: (date(2026, 1, 28), True),
    )
    args = parse_args(["--latest"])
    dates = resolve_dates(args)
    assert dates == [date(2026, 1, 28)]


def test_resolve_dates_latest_days_back(monkeypatch):
    """--latest --days-back 3 returns 3 dates ending at latest."""
    monkeypatch.setattr(
        "src.ingest.cli.availability.check_latest",
        lambda year=None: (date(2026, 1, 28), True),
    )
    args = parse_args(["--latest", "--days-back", "3"])
    dates = resolve_dates(args)
    assert dates == [date(2026, 1, 26), date(2026, 1, 27), date(2026, 1, 28)]


def test_resolve_dates_latest_no_data(monkeypatch):
    """--latest with no upstream data returns empty list."""
    monkeypatch.setattr(
        "src.ingest.cli.availability.check_latest",
        lambda year=None: (date.today(), False),
    )
    args = parse_args(["--latest"])
    dates = resolve_dates(args)
    assert dates == []


def test_latest_mutex_with_start_end():
    """--latest and --start/--end are mutually exclusive."""
    with pytest.raises(SystemExit):
        parse_args(["--latest", "--start", "2024-01-01", "--end", "2024-01-03"])


# --- cli: --on-empty ---

def test_on_empty_fail(monkeypatch, tmp_path):
    """--on-empty fail exits 1 when no records."""
    monkeypatch.setattr("src.ingest.client.fetch_day", lambda day, limit=None: [])
    monkeypatch.setattr(config, "RAW_DIR", str(tmp_path))
    with pytest.raises(SystemExit) as exc_info:
        from src.ingest.cli import main
        main(["--date", "2024-01-01", "--on-empty", "fail"])
    assert exc_info.value.code == 1


def test_on_empty_skip(monkeypatch, tmp_path):
    """--on-empty skip exits 0 when no records."""
    monkeypatch.setattr("src.ingest.client.fetch_day", lambda day, limit=None: [])
    monkeypatch.setattr(config, "RAW_DIR", str(tmp_path))
    from src.ingest.cli import main
    main(["--date", "2024-01-01", "--on-empty", "skip"])  # should not raise
