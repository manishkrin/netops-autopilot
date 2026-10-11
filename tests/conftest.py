from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
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

