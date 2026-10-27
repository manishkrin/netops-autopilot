from __future__ import annotations

import json
import urllib.request

import pytest

from netops_autopilot.simulator.cli import generate_alerts, main, send_alert


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



def _run_cli(monkeypatch: pytest.MonkeyPatch, *args: str) -> int:
    monkeypatch.setattr("sys.argv", ["netops-simulator", *args])
    return main()


def test_cli_submits_1000_events_with_duplicates_end_to_end(
    live_server: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = _run_cli(
        monkeypatch,
        "--target",
        f"{live_server}/v1/alerts",
        "--count",
        "1000",
        "--duplicate-every",
        "5",
        "--interval-ms",
        "0",
    )

    assert exit_code == 0
    summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert summary == {"submitted": 1000, "accepted": 800, "duplicates": 200, "failed": 0}
    with urllib.request.urlopen(f"{live_server}/v1/metrics") as response:  # noqa: S310
        assert json.load(response)["stored_events"] == 800


def test_cli_reports_failures_with_nonzero_exit(
    live_server: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = _run_cli(
        monkeypatch,
        "--target",
        f"{live_server}/v1/does-not-exist",
        "--count",
        "2",
        "--interval-ms",
        "0",
    )

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "submission failed (404)" in output
    assert '"failed": 2' in output


def test_send_alert_returns_validation_error_body(live_server: str) -> None:
    alert = next(generate_alerts(count=1))
    alert["severity"] = "bogus"

    code, body = send_alert(f"{live_server}/v1/alerts", alert)

    assert code == 422
    assert "severity" in body
