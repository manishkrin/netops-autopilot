from __future__ import annotations

import argparse
import json
import random
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

# Point-to-point links from the srl-telemetry-lab topology (st.clab.yml).
LAB_LINKS: tuple[tuple[str, str, str, str], ...] = (
    ("spine1", "e1-1", "leaf1", "e1-49"),
    ("spine1", "e1-2", "leaf2", "e1-49"),
    ("spine1", "e1-3", "leaf3", "e1-49"),
    ("spine2", "e1-1", "leaf1", "e1-50"),
    ("spine2", "e1-2", "leaf2", "e1-50"),
    ("spine2", "e1-3", "leaf3", "e1-50"),
    ("leaf1", "e1-1", "client1", "eth1"),
    ("leaf2", "e1-1", "client2", "eth1"),
    ("leaf3", "e1-1", "client3", "eth1"),
)
FAILURE_MODES: tuple[str, ...] = ("link-down", "admin-disable", "optic-failure", "peer-reboot")


def generate_alerts(
    *,
    count: int,
    duplicate_every: int = 0,
    run_id: str | None = None,
) -> Iterator[dict[str, Any]]:
    """Generate interface-flap submissions; every Nth can replay its predecessor."""
    if count < 1:
        raise ValueError("count must be at least 1")
    if duplicate_every == 1 or duplicate_every < 0:
        raise ValueError("duplicate_every must be 0 or at least 2")

    simulation_id = run_id or uuid.uuid4().hex[:12]
    base_time = datetime.now(UTC)
    previous_event_id: str | None = None
    rng = random.Random(simulation_id)  # noqa: S311 - synthetic data, not security-sensitive
    for index in range(count):
        is_duplicate = bool(duplicate_every and (index + 1) % duplicate_every == 0)
        event_id = previous_event_id if is_duplicate else f"sim-{simulation_id}-{index:05d}"
        if event_id is None:  # pragma: no cover - guarded by duplicate validation
            raise RuntimeError("Cannot generate a duplicate before an original event")
        if not is_duplicate:
            previous_event_id = event_id
        interface_up = index % 2 == 1
        if index % 2 == 0:  # each down/up pair shares one link and failure mode
            link = rng.choice(LAB_LINKS)
            failure_mode = rng.choice(FAILURE_MODES)
        device, interface, peer_device, peer_interface = link
        yield {
            "event_id": event_id,
            "source": "netops-simulator",
            "device": device,
            "interface": interface,
            "event_type": "interface_flap",
            "severity": "warning" if interface_up else "critical",
            "observed_at": (base_time + timedelta(milliseconds=index * 100)).isoformat(),
            "message": f"Interface changed state to {'up' if interface_up else 'down'}",
            "attributes": {
                "scenario": "interface-flap",
                "simulation_id": simulation_id,
                "sequence": index,
                "peer_device": peer_device,
                "peer_interface": peer_interface,
                "failure_mode": "recovered" if interface_up else failure_mode,
                "lab": "srl-telemetry-lab",
                "synthetic": True,
            },
        }


def send_alert(target: str, alert: dict[str, Any], timeout: float = 5.0) -> tuple[int, str]:
    payload = json.dumps(alert).encode()
    request = urllib.request.Request(
        target,
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            body = response.read().decode()
            return response.status, body
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate safe synthetic network alerts")
    parser.add_argument("--target", default="http://127.0.0.1:8000/v1/alerts")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--duplicate-every", type=int, default=0)
    parser.add_argument("--interval-ms", type=int, default=50)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    accepted = duplicates = failed = 0
    for alert in generate_alerts(count=args.count, duplicate_every=args.duplicate_every):
        code, body = send_alert(args.target, alert)
        if code == 202:
            accepted += 1
        elif code == 200:
            duplicates += 1
        else:
            failed += 1
            print(f"submission failed ({code}): {body}")
        if args.interval_ms:
            time.sleep(args.interval_ms / 1_000)
    print(
        json.dumps(
            {
                "submitted": args.count,
                "accepted": accepted,
                "duplicates": duplicates,
                "failed": failed,
            }
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

