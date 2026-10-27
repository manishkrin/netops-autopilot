# AI Agent Instructions & Context

This document gives coding agents the project context and constraints needed to make focused, safe changes. The root `README.md` is the step-by-step demo guide, `CHANGELOG.md` tracks changes, and the current progress, architecture, roadmap, and safety details live under `docs/`.

## System Overview

- **Purpose:** Evidence-first network incident investigation and approval-gated remediation.
- **Core stack:** Python 3.12+, FastAPI, Pydantic, SQLite, and `uv`.
- **Current release:** Alert validation, durable storage, duplicate detection, query and metrics endpoints, and a Grafana webhook adapter, and a synthetic alert simulator (random links and failure modes from the SR Linux lab topology) are implemented and tested.
- **Not implemented yet:** Correlation, investigation, AI analysis, approval, and remediation packages currently define boundaries for future work. Do not describe them as working features.
- **Network lab:** `srl-telemetry-lab-main/` is a separate Containerlab telemetry environment and is not automatically connected to the ingestion API.

## Development Rules

- Follow the existing modular-monolith boundaries under `src/netops_autopilot/`. Keep domain behavior in its owning package and avoid introducing service or framework complexity without a demonstrated need.
- Preserve the alert API contract, including `event_id` idempotency: repeated deliveries must not create another stored event.
- Add or update focused tests for behavior changes. Use the existing pytest and Ruff configuration; Python targets 3.12 and Ruff enforces a 100-character line length.
- Install dependencies and run checks with `uv`:

  ```bash
  uv sync --extra dev
  uv run ruff check .
  uv run pytest --cov --cov-report=term-missing
  ```

- Keep documentation aligned with the implementation. Update `README.md` when current capabilities or run instructions change; use `docs/` for architecture, roadmap, decisions, and benchmark evidence.

## Safety Constraints

- The current application is local and does not change network devices. Do not add device-changing behavior or connect the lab to execution paths without an explicitly scoped, authorized task.
- Use only synthetic, public, or explicitly authorized data and infrastructure. Never add proprietary configurations, incidents, customer data, or credentials to the repository.
- Treat webhook payloads, diagnostic output, and AI output as untrusted input. AI may propose analysis, but deterministic policy and explicit human approval must control any future network change.
- Never give an AI component credentials or unrestricted command execution. Any future executor must use a narrow, allow-listed action contract and auditable approval flow.
- Do not imply that a future lifecycle stage is implemented merely because its package or interface exists.

## Key References

- `src/netops_autopilot/api.py`: HTTP endpoints and application wiring.
- `src/netops_autopilot/ingestion/`: alert schemas, storage, and Grafana webhook adapter.
- `src/netops_autopilot/simulator/`: synthetic event generation and CLI; devices and links mirror the `srl-telemetry-lab-main` topology.
- `tests/`: API, ingestion, webhook, and simulator behavior tests.
- `docs/project-brief.md`: product goals, success measures, and guardrails.
- `docs/architecture.md`: module responsibilities, lifecycle, and threat boundaries.
- `docs/roadmap.md`: planned milestones and definitions of done.
- `docs/decisions/`: recorded architecture decisions.