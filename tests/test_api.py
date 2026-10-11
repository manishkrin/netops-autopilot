from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


def test_ingest_and_retrieve(client: TestClient, alert_payload: dict[str, object]) -> None:
    created = client.post("/v1/alerts", json=alert_payload)
    assert created.status_code == 202
    assert created.json()["status"] == "accepted"

    fetched = client.get(f"/v1/alerts/{alert_payload['event_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["device"] == "lab-router-01"


def test_duplicate_delivery_is_idempotent(
    client: TestClient, alert_payload: dict[str, object]
) -> None:
    first = client.post("/v1/alerts", json=alert_payload)
    second = client.post("/v1/alerts", json=alert_payload)

    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert second.json()["alert"]["received_at"] == first.json()["alert"]["received_at"]
    assert client.get("/v1/metrics").json()["stored_events"] == 1


def test_list_filters_by_device(client: TestClient, alert_payload: dict[str, object]) -> None:
    client.post("/v1/alerts", json=alert_payload)
    other = {**alert_payload, "event_id": "other-0001", "device": "lab-router-02"}
    client.post("/v1/alerts", json=other)

    response = client.get("/v1/alerts", params={"device": "lab-router-02"})

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["items"][0]["event_id"] == "other-0001"


def test_rejects_unknown_fields(client: TestClient, alert_payload: dict[str, object]) -> None:
    invalid = {**alert_payload, "execute_command": "reload"}
    response = client.post("/v1/alerts", json=invalid)
    assert response.status_code == 422


def test_requires_timezone_aware_timestamp(
    client: TestClient, alert_payload: dict[str, object]
) -> None:
    invalid = {**alert_payload, "observed_at": "2026-10-11T10:00:00"}
    response = client.post("/v1/alerts", json=invalid)
    assert response.status_code == 422


def test_missing_event_returns_404(client: TestClient) -> None:
    response = client.get("/v1/alerts/does-not-exist")
    assert response.status_code == 404

