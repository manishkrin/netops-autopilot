from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response, status

from netops_autopilot.config import Settings
from netops_autopilot.ingestion.grafana_adapter import to_alert_inputs
from netops_autopilot.ingestion.schemas import (
    AlertIngestResult,
    AlertInput,
    AlertList,
    AlertRecord,
    GrafanaWebhookPayload,
    IngestionMetrics,
    WebhookIngestResult,
)
from netops_autopilot.ingestion.store import SQLiteAlertStore
from netops_autopilot.logging import configure_logging

LOGGER = logging.getLogger("netops_autopilot.api")


def create_app(database_path: Path | None = None) -> FastAPI:
    settings = Settings.from_environment()
    if database_path is not None:
        settings = Settings(database_path=database_path, log_level=settings.log_level)
    configure_logging(settings.log_level)
    store = SQLiteAlertStore(settings.database_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
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
        items: list[AlertIngestResult] = []
        accepted = 0
        duplicate = 0
        for alert in to_alert_inputs(payload.alerts):
            stored, created = store.ingest(alert)
            if created:
                accepted += 1
            else:
                duplicate += 1
            items.append(
                AlertIngestResult(status="accepted" if created else "duplicate", alert=stored)
            )
        return WebhookIngestResult(
            received=len(items), accepted=accepted, duplicate=duplicate, items=items
        )

    @application.get("/v1/alerts", response_model=AlertList, tags=["ingestion"])
    def list_alerts(
        device: str | None = None,
        event_type: str | None = None,
        limit: int = Query(default=100, ge=1, le=1_000),
    ) -> AlertList:
        items = store.list(device=device, event_type=event_type, limit=limit)
        return AlertList(items=items, count=len(items))

    @application.get("/v1/alerts/{event_id}", response_model=AlertRecord, tags=["ingestion"])
    def get_alert(event_id: str) -> AlertRecord:
        alert = store.get(event_id)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    @application.get("/v1/metrics", response_model=IngestionMetrics, tags=["operations"])
    def metrics() -> IngestionMetrics:
        total, by_severity = store.metrics()
        return IngestionMetrics(stored_events=total, by_severity=by_severity)

    return application


app = create_app()

