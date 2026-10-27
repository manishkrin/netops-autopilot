# Six-month roadmap

Each month ends with a demonstrable capability and evidence. Features do not advance merely because their code exists.

## Current progress

Month 1 is substantially complete; later months have only package boundaries.

| Month 1 item | Status |
|---|---|
| API, durable SQLite storage, duplicate handling, health/metrics endpoints | Done |
| Synthetic interface-flap simulator using SR Linux lab links and failure modes | Done |
| Grafana webhook adapter | Implemented; not verified end to end against a running lab |
| Tests, CI, clean-checkout demo (`scripts/demo.py`, README steps) | Done |
| 1,000-submission benchmark | Local sequential baseline recorded in `docs/benchmarks/` |
| Telemetry lab wired to the API | Manual steps documented in README; not automated |
| Months 2–6 (correlation through production evidence) | Not started |

## Month 1 — simulator, webhook, and event store

Ship the Python API, synthetic interface-flap generator, durable event storage, idempotent duplicate handling, health/metrics endpoints, tests, CI, and local run instructions.

Definition of done:

- 1,000 synthetic event submissions complete successfully.
- Duplicate `event_id` deliveries result in one stored event.
- Invalid inputs produce useful validation errors.
- A clean checkout can run tests and the demo.
- The benchmark command and environment are recorded; no results are invented.

## Month 2 — correlation

Add rule-based time-window grouping, incident records, late-arriving event handling, explainable rule metadata, and fixtures for storms, duplicates, unrelated alerts, and topology-adjacent devices.

Definition of done:

- The 25-alert interface-flap scenario becomes one incident.
- Precision and recall are measured against labeled synthetic scenarios.
- Reprocessing is idempotent and deterministic.

## Month 3 — investigation

Create a simulated network adapter, diagnostic plans, evidence records, topology/interface history, timeouts, partial-failure behavior, and reproducible investigation fixtures.

Definition of done:

- An incident triggers an allow-listed diagnostic plan.
- Findings cite immutable evidence IDs.
- Failed diagnostics remain visible and do not silently become negative evidence.

## Month 4 — structured AI analysis

Add a provider-neutral analysis interface, schema-validated hypotheses, evidence citation validation, confidence and alternatives, prompt/model versioning, deterministic mock responses, and an evaluation dataset.

Definition of done:

- Outputs cannot reference nonexistent evidence.
- Invalid or unsupported model responses fail closed.
- Evaluation reports measure groundedness, schema compliance, and useful uncertainty.

## Month 5 — approval-gated Ansible

Implement remediation proposals, deterministic policy checks, approval state transitions, allow-listed Ansible runner integration, execution idempotency, verification, audit events, and one rollback-capable lab workflow.

Definition of done:

- No workflow runs without valid policy and approval records.
- A repeated execution key cannot apply a change twice.
- One safe remediation demonstrates success, failed verification, and rollback.

## Month 6 — production evidence and public demo

Complete the test pyramid, OpenTelemetry instrumentation, infrastructure as code, failure injection, load and recovery tests, threat model, operator docs, benchmark report, and recorded end-to-end demo.

Definition of done:

- Reproducible deployment from documented infrastructure definitions.
- Published throughput, latency, resource use, and recovery results with environment details.
- Demonstration covers alert through verified remediation and an intentional failure path.
- Known limitations and next decisions are explicit.

## Weekly operating rule

Use a backlog for new ideas. Only accept work that materially advances the current month's definition of done or removes a demonstrated blocker. Do not add a frontend, multi-agent system, or elaborate RAG layer before the core lifecycle is proven.

