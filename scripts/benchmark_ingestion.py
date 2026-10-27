from __future__ import annotations

import argparse
import json
import os
import platform
import sqlite3
import statistics
import subprocess
import sys
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from netops_autopilot.simulator.cli import generate_alerts, send_alert

REPO_ROOT = Path(__file__).resolve().parent.parent


def percentile(samples: list[float], fraction: float) -> float:
    ordered = sorted(samples)
    index = min(round((len(ordered) - 1) * fraction), len(ordered) - 1)
    return ordered[index]


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def collect_environment() -> dict[str, Any]:
    """Describe the machine and code under test; unavailable values are recorded as null."""
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "working_tree_dirty": None if status is None else bool(status),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        # Describes the client interpreter; it matches the server only if both run from
        # the same environment, which the operator must confirm.
        "client_sqlite_version": sqlite3.sqlite_version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
    }


def metrics_url(target: str) -> str:
    parts = urlsplit(target)
    return urlunsplit((parts.scheme, parts.netloc, "/v1/metrics", "", ""))


def stored_event_count(target: str) -> int | None:
    try:
        with urllib.request.urlopen(metrics_url(target), timeout=5) as response:  # noqa: S310
            return int(json.load(response)["stored_events"])
    except (OSError, ValueError, KeyError):
        return None


def run(target: str, count: int) -> dict[str, Any]:
    latencies: list[float] = []
    statuses: dict[int, int] = {}
    stored_before = stored_event_count(target)
    started = time.perf_counter()
    for alert in generate_alerts(count=count):
        request_started = time.perf_counter()
        code, _ = send_alert(target, alert)
        latencies.append((time.perf_counter() - request_started) * 1_000)
        statuses[code] = statuses.get(code, 0) + 1
    duration = time.perf_counter() - started
    stored_after = stored_event_count(target)
    stored_delta = (
        None if stored_before is None or stored_after is None else stored_after - stored_before
    )
    return {
        "recorded_at": datetime.now(UTC).isoformat(),
        "environment": collect_environment(),
        "target": target,
        "workload": "sequential unique interface-flap events, no warm-up, single run",
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
        "stored_event_count_before_run": stored_before,
        "stored_event_count_after_run": stored_after,
        "stored_event_delta": stored_delta,
        "verified": statuses == {202: count} and stored_delta == count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sequential ingestion baseline")
    parser.add_argument("--target", default="http://127.0.0.1:8000/v1/alerts")
    parser.add_argument("--count", type=int, default=1_000)
    parser.add_argument("--out", type=Path, help="also write the raw JSON result to this file")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be at least 1")
    result = run(args.target, args.count)
    output = json.dumps(result, indent=2)
    print(output)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n")
    if not result["verified"]:
        print(
            "NOT VERIFIED: expected every response to be 202 and the stored count to grow "
            "by the submission count",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
