#!/usr/bin/env bash
set -euo pipefail

# Use venv if available
if [ -f ".venv/bin/python3" ]; then
  export PATH=".venv/bin:$PATH"
fi

echo "== git status =="
git status --porcelain=v1 || true

echo "== python version =="
python3 -c "import sys; print(sys.version)"

echo "== pip deps =="
python3 -c "import requests; print('requests', requests.__version__)" || { echo "FAIL: requests not installed"; exit 1; }

echo "== pytest =="
python3 -m pytest tests/ -q || { echo "FAIL: tests"; exit 1; }

echo "== ingest smoke test =="
python3 -m src.ingest.cli --date 2024-01-15 --limit 5
test -f data/raw/date=2024-01-15/la311_20240115.jsonl.gz && echo "ingest smoke ok" || { echo "FAIL: ingest smoke"; exit 1; }

echo "== docker compose =="
docker compose version >/dev/null 2>&1 && echo "docker compose ok" || echo "docker compose unavailable (ok for now)"

echo ""
echo "VERIFY DONE ✓"
