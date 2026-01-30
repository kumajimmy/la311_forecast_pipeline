"""Unit tests for the ingestion module."""

import gzip
import json
from datetime import date
from pathlib import Path
from unittest import mock

import pytest

from src.ingest import config, writer
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
