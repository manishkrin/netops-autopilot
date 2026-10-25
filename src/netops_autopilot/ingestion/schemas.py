from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


EventId = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")]
Label = Annotated[str, Field(min_length=1, max_length=128)]


class AlertInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    event_id: EventId
    source: Label
    device: Label
    interface: str | None = Field(default=None, max_length=128)
    event_type: Label
    severity: Severity
    observed_at: AwareDatetime
    message: str = Field(min_length=1, max_length=2_000)
    attributes: dict[str, Any] = Field(default_factory=dict)


class AlertRecord(AlertInput):
    received_at: datetime


class AlertIngestResult(BaseModel):
    status: Literal["accepted", "duplicate"]
    alert: AlertRecord


class AlertList(BaseModel):
    items: list[AlertRecord]
    count: int


class IngestionMetrics(BaseModel):
    stored_events: int
    by_severity: dict[str, int]


class GrafanaAlert(BaseModel):
    """A single alert entry from Grafana's unified-alerting webhook payload.

    Only the fields needed for translation into ``AlertInput`` are declared;
    unknown fields are ignored since Grafana's payload carries many extras
    (generatorURL, silenceURL, dashboardURL, values, ...).
    """

    model_config = ConfigDict(extra="ignore")

    status: Literal["firing", "resolved"]
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: AwareDatetime
    endsAt: AwareDatetime | None = None
    fingerprint: str = Field(min_length=1, max_length=128)


class GrafanaWebhookPayload(BaseModel):
    """Top-level body Grafana sends to a `webhook` contact point."""

    model_config = ConfigDict(extra="ignore")

    alerts: list[GrafanaAlert] = Field(default_factory=list)


class WebhookIngestResult(BaseModel):
    received: int
    accepted: int
    duplicate: int
    items: list[AlertIngestResult]

