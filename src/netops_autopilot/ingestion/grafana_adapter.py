"""Translate Grafana unified-alerting webhook payloads into AlertInput records.

Grafana's "webhook" contact point does not speak the same JSON shape as our
`/v1/alerts` ingestion endpoint (see docs/architecture.md: "Webhook payloads
... are untrusted"), so each alert entry is mapped explicitly rather than
passed through.
"""

from __future__ import annotations

from datetime import datetime

from netops_autopilot.ingestion.schemas import AlertInput, GrafanaAlert, Severity

_KNOWN_SEVERITIES = {severity.value for severity in Severity}
_DEFAULT_SEVERITY = Severity.WARNING


def _resolve_severity(labels: dict[str, str]) -> Severity:
    candidate = labels.get("severity", "").lower()
    if candidate in _KNOWN_SEVERITIES:
        return Severity(candidate)
    return _DEFAULT_SEVERITY


def _resolve_observed_at(alert: GrafanaAlert) -> datetime:
    if alert.status == "resolved" and alert.endsAt is not None:
        return alert.endsAt
    return alert.startsAt


def to_alert_input(alert: GrafanaAlert) -> AlertInput:
    """Map a single Grafana alert entry to our strongly-typed AlertInput."""
    labels = alert.labels
    annotations = alert.annotations
    alert_name = labels.get("alertname", "grafana_alert")
    device = labels.get("node") or labels.get("instance") or "unknown"
    interface = labels.get("interface_name")

    message = (
        annotations.get("summary")
        or annotations.get("description")
        or f"Grafana alert '{alert_name}' is {alert.status}"
    )

    return AlertInput(
        event_id=f"grafana-{alert.fingerprint}-{alert.status}",
        source="grafana",
        device=device,
        interface=interface,
        event_type=alert_name,
        severity=_resolve_severity(labels),
        observed_at=_resolve_observed_at(alert),
        message=message,
        attributes={
            "status": alert.status,
            "labels": labels,
            "annotations": annotations,
            "fingerprint": alert.fingerprint,
        },
    )


def to_alert_inputs(alerts: list[GrafanaAlert]) -> list[AlertInput]:
    return [to_alert_input(alert) for alert in alerts]
