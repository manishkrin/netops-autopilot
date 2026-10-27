from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient

from netops_autopilot.api import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(tmp_path / "events.db")) as test_client:
        yield test_client


@pytest.fixture
def alert_payload() -> dict[str, object]:
    return {
        "event_id": "lab-router-01-interface-0001",
        "source": "test-suite",
        "device": "lab-router-01",
        "interface": "GigabitEthernet0/1",
        "event_type": "interface_flap",
        "severity": "critical",
        "observed_at": "2026-10-11T10:00:00Z",
        "message": "Interface changed state to down",
        "attributes": {"synthetic": True},
    }


@pytest.fixture
def live_server(tmp_path: Path) -> Iterator[str]:
    """Run the real app under uvicorn on a free loopback port; yield its base URL."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(tmp_path / "live.db"),
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started:
        if time.monotonic() > deadline:  # pragma: no cover - startup failure
            raise RuntimeError("uvicorn did not start")
        time.sleep(0.01)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)

