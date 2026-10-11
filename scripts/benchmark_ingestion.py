from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import UTC, datetime
from typing import Any

from netops_autopilot.simulator.cli import generate_alerts, send_alert


def percentile(samples: list[float], fraction: float) -> float:
    ordered = sorted(samples)
    index = min(round((len(ordered) - 1) * fraction), len(ordered) - 1)
    return ordered[index]


def run(target: str, count: int) -> dict[str, Any]:
    latencies: list[float] = []
    statuses: dict[int, int] = {}
    started = time.perf_counter()
    for alert in generate_alerts(count=count):
        request_started = time.perf_counter()
        code, _ = send_alert(target, alert)
        latencies.append((time.perf_counter() - request_started) * 1_000)
        statuses[code] = statuses.get(code, 0) + 1
    duration = time.perf_counter() - started
    return {
        "recorded_at": datetime.now(UTC).isoformat(),
        "target": target,
        "submission_count": count,
        "duration_seconds": round(duration, 3),
        "throughput_per_second": round(count / duration, 2),
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 2),
            "p50": round(percentile(latencies, 0.50), 2),
            "p95": round(percentile(latencies, 0.95), 2),
            "p99": round(percentile(latencies, 0.99), 2),
        },
        "http_status_counts": statuses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sequential ingestion baseline")
    parser.add_argument("--target", default="http://127.0.0.1:8000/v1/alerts")
    parser.add_argument("--count", type=int, default=1_000)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be at least 1")
    print(json.dumps(run(args.target, args.count), indent=2))


if __name__ == "__main__":
    main()

