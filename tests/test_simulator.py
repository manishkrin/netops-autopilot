from __future__ import annotations

import pytest

from netops_autopilot.simulator.cli import generate_alerts


def test_generates_requested_interface_flap_submissions() -> None:
    alerts = list(generate_alerts(count=3, run_id="unit-test"))
    assert len(alerts) == 3
    assert len({alert["event_id"] for alert in alerts}) == 3
    assert all(alert["attributes"]["synthetic"] for alert in alerts)


def test_can_generate_duplicate_deliveries() -> None:
    alerts = list(generate_alerts(count=5, duplicate_every=2, run_id="unit-test"))
    assert [alert["event_id"] for alert in alerts] == [
        "sim-unit-test-00000",
        "sim-unit-test-00000",
        "sim-unit-test-00002",
        "sim-unit-test-00002",
        "sim-unit-test-00004",
    ]


@pytest.mark.parametrize("duplicate_every", [-1, 1])
def test_rejects_invalid_duplicate_interval(duplicate_every: int) -> None:
    with pytest.raises(ValueError):
        list(generate_alerts(count=3, duplicate_every=duplicate_every))

