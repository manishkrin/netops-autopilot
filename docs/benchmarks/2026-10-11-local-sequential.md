# Local sequential ingestion baseline — 2026-10-11

## Purpose

Verify the month-one acceptance target that 1,000 synthetic alert submissions can be accepted and durably stored. This run is not a capacity claim.

## Environment

- Platform: macOS 27.0.1, arm64
- Python: CPython 3.14.2
- SQLite: 3.50.4, local file with WAL enabled
- API: one local Uvicorn process on loopback
- Client: sequential standard-library HTTP requests
- Workload: 1,000 unique synthetic interface-flap events
- Warm-up: none
- Run count: one

## Command

```bash
uv run python scripts/benchmark_ingestion.py \
  --target http://127.0.0.1:8765/v1/alerts \
  --count 1000
```

## Result

```json
{
  "recorded_at": "2026-10-11T13:55:37.464277+00:00",
  "submission_count": 1000,
  "duration_seconds": 1.275,
  "throughput_per_second": 784.44,
  "latency_ms": {
    "mean": 1.27,
    "p50": 1.17,
    "p95": 1.52,
    "p99": 2.79
  },
  "http_status_counts": {
    "202": 1000
  },
  "stored_event_count_after_run": 1000
}
```

## Interpretation

All 1,000 submissions returned the expected accepted status and the database contained 1,000 rows after the run. This proves the initial correctness target in this environment. It does not establish concurrent throughput, production latency, maximum capacity, resource efficiency, or recovery behavior. Later benchmarks must use repeated controlled trials and retain raw data.

