#!/usr/bin/env bash
set -euo pipefail

# Use venv if available (optional)
if [ -f ".venv/bin/python3" ]; then
  export PATH=".venv/bin:$PATH"
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "== git status =="
git status --porcelain=v1 || true

echo "== python version =="
$PYTHON_BIN -c "import sys; print(sys.version)"

echo "== pip deps =="
$PYTHON_BIN -c "import requests; print('requests', requests.__version__)" || { echo "FAIL: requests not installed"; exit 1; }
$PYTHON_BIN -c "import pytest; print('pytest', pytest.__version__)" || { echo "FAIL: pytest not installed"; exit 1; }

echo "== pytest =="
$PYTHON_BIN -m pytest tests/ -q || { echo "FAIL: tests"; exit 1; }

echo "== ingest smoke test =="

# IMPORTANT:
# - Use a stable, known-good date + dataset so verify doesn't break in a new calendar year.
# - Override WITHOUT touching your normal LA311_API_BASE by using:
#     LA311_VERIFY_API_BASE=... LA311_VERIFY_SMOKE_DATE=... make verify
#
# Default smoke dataset: MyLA311 Service Request Data 2024 (API endpoint)
# Default smoke date: a date that should have records.
export LA311_API_BASE="${LA311_VERIFY_API_BASE:-https://data.lacity.org/resource/b7dx-7gc3.json}"
SMOKE_DATE="${LA311_VERIFY_SMOKE_DATE:-2024-01-15}"

$PYTHON_BIN -m src.ingest.cli --date "$SMOKE_DATE" --limit 5

SMOKE_YYYYMMDD="${SMOKE_DATE//-/}"
OUT_FILE="data/raw/date=$SMOKE_DATE/la311_${SMOKE_YYYYMMDD}.jsonl.gz"

if [ ! -f "$OUT_FILE" ]; then
  echo "FAIL: ingest smoke (missing $OUT_FILE)"
  exit 1
fi

LINECOUNT=$(gzip -cd "$OUT_FILE" | wc -l | tr -d ' ')
if [ "$LINECOUNT" -lt 1 ]; then
  echo "FAIL: ingest smoke (empty file)"
  exit 1
fi

echo "ingest smoke ok ($LINECOUNT lines)"

echo "== docker compose =="
docker compose version >/dev/null 2>&1 && echo "docker compose ok" || echo "docker compose unavailable (ok for now)"

echo ""
echo "VERIFY DONE ✓"