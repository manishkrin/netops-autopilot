from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from pydantic import ValidationError

from netops_autopilot.config import Settings
from netops_autopilot.ingestion.grafana_adapter import describe_validation_error, to_alert_input
from netops_autopilot.ingestion.schemas import (
    AlertIngestResult,
    AlertInput,
    AlertList,
    AlertRecord,
    GrafanaWebhookPayload,
    IngestionMetrics,
    WebhookIngestResult,
    WebhookRejection,
)
from netops_autopilot.ingestion.store import SQLiteAlertStore
from netops_autopilot.logging import configure_logging

LOGGER = logging.getLogger("netops_autopilot.api")


def create_app(database_path: Path | None = None) -> FastAPI:
    """Build and configure the NetOps Autopilot FastAPI application.

    Loads settings from the environment (optionally overriding the database
    path), configures logging, wires up the SQLite-backed alert store, and
    registers the lifespan hook, middleware, and all HTTP routes.

    Args:
        database_path: Optional override for the SQLite database path. When
            provided, it replaces the value derived from the environment.

    Returns:
        A fully configured ``FastAPI`` application instance.
    """
    settings = Settings.from_environment()
    if database_path is not None:
        settings = Settings(database_path=database_path, log_level=settings.log_level)
    configure_logging(settings.log_level)
    store = SQLiteAlertStore(settings.database_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        """Initialize the alert store on application startup.

        Runs once before the application begins serving requests, ensuring
        the SQLite store's schema is created/ready, then yields control for
        the lifetime of the application.
        """
        store.initialize()
        yield

    application = FastAPI(
        title="NetOps Autopilot",
        version="0.1.0",
        description="Evidence-first, approval-gated network operations automation.",
        lifespan=lifespan,
    )
    application.state.alert_store = store

    @application.middleware("http")
    async def request_logging(request: Request, call_next):  # type: ignore[no-untyped-def]
        """Log request/response metadata and attach a request ID header.

        Generates (or reuses) an ``x-request-id`` value, times the downstream
        handler, echoes the request ID back on the response, and emits a
        structured log record summarizing the completed request.

        Args:
            request: The incoming HTTP request.
            call_next: Callable that invokes the next middleware/handler and
                returns the resulting response.

        Returns:
            The response produced by the downstream handler, with the
            ``x-request-id`` header set.
        """
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        LOGGER.info(
            "request_completed",
            extra={
                "fields": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            },
        )
        return response

    @application.get("/health", tags=["operations"])
    def health() -> dict[str, str]:
        """Report service health based on alert store availability.

        Returns:
            A dict with ``status: "ok"`` when the store responds to a ping.

        Raises:
            HTTPException: With status 503 if the event store is unavailable.
        """
        if not store.ping():
            raise HTTPException(status_code=503, detail="Event store is unavailable")
        return {"status": "ok"}

    @application.post(
        "/v1/alerts",
        response_model=AlertIngestResult,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["ingestion"],
    )
    def ingest_alert(alert: AlertInput, response: Response) -> AlertIngestResult:
        """Ingest a single alert into the store.

        If the alert has already been recorded (a duplicate), the response
        status is downgraded from 202 Accepted to 200 OK.

        Args:
            alert: The alert payload to ingest.
            response: The outgoing response, mutated to reflect duplicate
                ingestion when applicable.

        Returns:
            The ingestion result containing the stored alert and its status
            (``"accepted"`` or ``"duplicate"``).
        """
        stored, created = store.ingest(alert)
        if not created:
            response.status_code = status.HTTP_200_OK
        return AlertIngestResult(
            status="accepted" if created else "duplicate",
            alert=stored,
        )

    @application.post(
        "/v1/webhooks/grafana",
        response_model=WebhookIngestResult,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["ingestion"],
    )
    def ingest_grafana_webhook(payload: GrafanaWebhookPayload) -> WebhookIngestResult:
        """Ingest a batch of alerts from a Grafana webhook payload.

        Converts the incoming Grafana alerts into internal alert inputs,
        ingests each one, and tallies how many were newly accepted versus
        duplicates. An alert that cannot be mapped to a valid internal alert
        (for example an over-long label) is reported in ``rejections`` and does
        not prevent the rest of the batch from being stored, so Grafana does
        not retry the whole payload.

        Args:
            payload: The Grafana webhook payload containing one or more
                alerts.

        Returns:
            A summary of the webhook ingestion, including per-alert results,
            rejected alerts, and aggregate accepted/duplicate/rejected counts.
        """
        items: list[AlertIngestResult] = []
        rejections: list[WebhookRejection] = []
        accepted = 0
        duplicate = 0
        for index, grafana_alert in enumerate(payload.alerts):
            try:
                alert = to_alert_input(grafana_alert)
            except ValidationError as error:
                rejection = WebhookRejection(
                    index=index,
                    fingerprint=grafana_alert.fingerprint,
                    errors=describe_validation_error(error),
                )
                LOGGER.warning(
                    "webhook_alert_rejected",
                    extra={"fields": {"index": index, "errors": rejection.errors}},
                )
                rejections.append(rejection)
                continue
            stored, created = store.ingest(alert)
            if created:
                accepted += 1
            else:
                duplicate += 1
            items.append(
                AlertIngestResult(status="accepted" if created else "duplicate", alert=stored)
            )
        return WebhookIngestResult(
            received=len(payload.alerts),
            accepted=accepted,
            duplicate=duplicate,
            rejected=len(rejections),
            items=items,
            rejections=rejections,
        )

    @application.get("/v1/alerts", response_model=AlertList, tags=["ingestion"])
    def list_alerts(
        device: str | None = None,
        event_type: str | None = None,
        limit: int = Query(default=100, ge=1, le=1000),
    ) -> AlertList:
        """List stored alerts, optionally filtered by device and event type.

        Args:
            device: Optional device name to filter alerts by.
            event_type: Optional event type to filter alerts by.
            limit: Maximum number of alerts to return (1-1000, default 100).

        Returns:
            The matching alerts along with the count of items returned.
        """
        items = store.list(device=device, event_type=event_type, limit=limit)
        return AlertList(items=items, count=len(items))

    @application.get("/v1/alerts/{event_id}", response_model=AlertRecord, tags=["ingestion"])
    def get_alert(event_id: str) -> AlertRecord:
        """Retrieve a single alert by its event ID.

        Args:
            event_id: The unique identifier of the alert event.

        Returns:
            The matching alert record.

        Raises:
            HTTPException: With status 404 if no alert exists for the given ID.
        """
        alert = store.get(event_id)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    @application.get("/v1/metrics", response_model=IngestionMetrics, tags=["operations"])
    def metrics() -> IngestionMetrics:
        """Return aggregate ingestion metrics.

        Returns:
            The total number of stored events and a breakdown of counts by
            severity.
        """
        total, by_severity = store.metrics()
        return IngestionMetrics(stored_events=total, by_severity=by_severity)

    return application


app = create_app()

