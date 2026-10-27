"""Run the Month 1 demo end to end on a throwaway database and assert its outcome.

Starts the API on a free loopback port, sends synthetic interface-flap alerts with
replayed duplicates, then checks the stored count through the API. Exits non-zero on any
mismatch, so it doubles as a clean-checkout smoke test in CI.

    uv run python scripts/demo.py
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310
        return json.load(response)


def _wait_until_healthy(base_url: str, server: subprocess.Popen[bytes], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"API exited early with code {server.returncode}")
        try:
            if _get_json(f"{base_url}/health").get("status") == "ok":
                return
        except (OSError, ValueError):
            time.sleep(0.1)
    raise RuntimeError("API did not become healthy in time")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--duplicate-every", type=int, default=5)
    args = parser.parse_args()

    duplicates = args.count // args.duplicate_every if args.duplicate_every else 0
    expected = args.count - duplicates

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="netops-demo-") as workdir:
        env = {
            **os.environ,
            "NETOPS_DATABASE_PATH": str(Path(workdir) / "demo.db"),
            "NETOPS_LOG_LEVEL": "WARNING",
        }
        server = subprocess.Popen(  # noqa: S603
            [
                sys.executable,
                "-m",
                "uvicorn",
                "netops_autopilot.api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--log-level",
                "warning",
            ],
            env=env,
        )
        try:
            _wait_until_healthy(base_url, server, timeout=30)
            print(f"API healthy at {base_url}; sending {args.count} alerts")
            simulator = subprocess.run(  # noqa: S603
                [
                    sys.executable,
                    "-m",
                    "netops_autopilot.simulator.cli",
                    "--target",
                    f"{base_url}/v1/alerts",
                    "--count",
                    str(args.count),
                    "--duplicate-every",
                    str(args.duplicate_every),
                    "--interval-ms",
                    "0",
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            print(simulator.stdout.strip())
            if simulator.returncode != 0:
                print(simulator.stderr, file=sys.stderr)
                return 1

            summary = json.loads(simulator.stdout.strip().splitlines()[-1])
            stored = _get_json(f"{base_url}/v1/metrics")["stored_events"]
            problems = []
            if summary["accepted"] != expected:
                problems.append(f"accepted {summary['accepted']}, expected {expected}")
            if summary["duplicates"] != duplicates:
                problems.append(f"duplicates {summary['duplicates']}, expected {duplicates}")
            if stored != expected:
                problems.append(f"stored {stored}, expected {expected}")
            if problems:
                print("DEMO FAILED: " + "; ".join(problems), file=sys.stderr)
                return 1
            print(f"DEMO OK: {summary['submitted']} submitted -> {stored} stored events")
            return 0
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:  # pragma: no cover
                server.kill()


if __name__ == "__main__":
    raise SystemExit(main())
