from __future__ import annotations

from fastapi.testclient import TestClient


def _grafana_payload(status: str = "firing") -> dict[str, object]:
    return {
        "receiver": "netops-autopilot",
        "status": status,
        "orgId": 1,
        "alerts": [
            {
                "status": status,
                "labels": {
                    "alertname": "Leaf1 Interface Down",
                    "node": "leaf1",
                    "interface_name": "e1-49",
                    "severity": "critical",
                },
                "annotations": {
                    "summary": "Interface e1-49 on leaf1 is DOWN",
                    "description": "interface_oper_state reported 0 (down).",
                },
                "startsAt": "2026-10-23T10:00:00Z",
                "endsAt": (
                    "2026-10-23T10:05:00Z" if status == "resolved" else "0001-01-01T00:00:00Z"
                ),
                "generatorURL": "http://grafana/alerting/grafana/leaf1-iface-down/view",
                "fingerprint": "abc123def456",
            }
        ],
        "groupLabels": {"alertname": "Leaf1 Interface Down"},
        "commonLabels": {"alertname": "Leaf1 Interface Down"},
        "commonAnnotations": {},
        "externalURL": "http://grafana/",
        "version": "1",
        "groupKey": "leaf1-iface-down",
        "title": "[FIRING:1] Leaf1 Interface Down",
        "message": "Leaf1 Interface Down",
    }


def test_grafana_webhook_ingests_firing_alert(client: TestClient) -> None:
    response = client.post("/v1/webhooks/grafana", json=_grafana_payload("firing"))

    assert response.status_code == 202
    body = response.json()
    assert body["received"] == 1
    assert body["accepted"] == 1
    assert body["duplicate"] == 0

    stored = body["items"][0]["alert"]
    assert stored["device"] == "leaf1"
    assert stored["interface"] == "e1-49"
    assert stored["severity"] == "critical"
    assert stored["source"] == "grafana"
    assert stored["event_type"] == "Leaf1 Interface Down"
    assert stored["attributes"]["status"] == "firing"
    assert stored["event_id"] == "grafana-abc123def456-firing"


def test_grafana_webhook_is_idempotent_on_redelivery(client: TestClient) -> None:
    payload = _grafana_payload("firing")

    first = client.post("/v1/webhooks/grafana", json=payload)
    second = client.post("/v1/webhooks/grafana", json=payload)

    assert first.json()["accepted"] == 1
    assert second.json()["accepted"] == 0
    assert second.json()["duplicate"] == 1


def test_grafana_webhook_tracks_firing_and_resolved_separately(client: TestClient) -> None:
    firing = client.post("/v1/webhooks/grafana", json=_grafana_payload("firing"))
    resolved = client.post("/v1/webhooks/grafana", json=_grafana_payload("resolved"))

    assert firing.json()["accepted"] == 1
    assert resolved.json()["accepted"] == 1

    metrics = client.get("/v1/metrics").json()
    assert metrics["stored_events"] == 2


def test_grafana_webhook_defaults_severity_when_label_missing(client: TestClient) -> None:
    payload = _grafana_payload("firing")
    del payload["alerts"][0]["labels"]["severity"]  # type: ignore[index]

    response = client.post("/v1/webhooks/grafana", json=payload)

    assert response.json()["items"][0]["alert"]["severity"] == "warning"


def test_grafana_webhook_rejects_malformed_payload(client: TestClient) -> None:
    response = client.post("/v1/webhooks/grafana", json={"alerts": [{"status": "unknown"}]})
    assert response.status_code == 422
