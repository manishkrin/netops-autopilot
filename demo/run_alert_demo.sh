#!/usr/bin/env bash
# Start the API on a persistent SQLite DB, send simulated alerts (with duplicates),
# print the stored rows, and leave the DB in place for inspection.
#
# Usage: demo/run_alert_demo.sh [COUNT] [DUPLICATE_EVERY]
set -euo pipefail

cd "$(dirname "$0")/.."

COUNT="${1:-25}"
DUP_EVERY="${2:-5}"
PORT="${PORT:-8000}"
export NETOPS_DATABASE_PATH="${NETOPS_DATABASE_PATH:-var/netops-autopilot.db}"
BASE_URL="http://127.0.0.1:${PORT}"

uv run uvicorn netops_autopilot.api:app --host 127.0.0.1 --port "$PORT" --log-level warning &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true; wait "$SERVER_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 100); do
  if curl -fs "${BASE_URL}/health" >/dev/null 2>&1; then break; fi
  kill -0 "$SERVER_PID" 2>/dev/null || { echo "API exited early" >&2; exit 1; }
  sleep 0.3
done
curl -fs "${BASE_URL}/health" >/dev/null || { echo "API not healthy" >&2; exit 1; }

echo "Sending ${COUNT} alerts to ${BASE_URL}/v1/alerts (duplicate every ${DUP_EVERY})"
uv run python -m netops_autopilot.simulator.cli \
  --target "${BASE_URL}/v1/alerts" \
  --count "$COUNT" \
  --duplicate-every "$DUP_EVERY" \
  --interval-ms 0

echo
echo "Database: ${NETOPS_DATABASE_PATH}"
uv run python - <<'PY'
import os
import sqlite3

con = sqlite3.connect(os.environ["NETOPS_DATABASE_PATH"])
print("alerts stored:", con.execute("SELECT COUNT(*) FROM alerts").fetchone()[0])
for row in con.execute(
    "SELECT device, interface, event_type, severity, observed_at FROM alerts "
    "ORDER BY received_at DESC LIMIT 10"
):
    print(row)
PY
