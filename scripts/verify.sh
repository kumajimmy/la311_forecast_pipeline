#!/usr/bin/env bash
set -euo pipefail

echo "== git status =="
git status --porcelain=v1 || true

echo "== python version =="
python3 -c "import sys; print(sys.version)"

echo "== pytest (optional early) =="
python3 -m pytest -q || echo "pytest not set up yet (ok for now)"

echo "== docker compose =="
docker compose version >/dev/null 2>&1 && echo "docker compose ok" || echo "docker compose unavailable"

echo "VERIFY DONE"
