# Architecture

## Principles

1. **Evidence before explanation.** Diagnostics create immutable evidence records before AI analysis begins.
2. **Uncertainty is part of the output.** A hypothesis includes confidence, alternatives, missing evidence, and evidence references.
3. **AI proposes; deterministic controls decide.** Code-based policy and a human approver control execution.
4. **At-least-once delivery is expected.** Event ingestion and automation execution use explicit idempotency keys.
5. **Every transition is auditable.** Actor, input, decision, timestamp, and outcome are recorded.
6. **Start as a modular monolith.** Clear package boundaries allow later extraction only when measurements demand it.

## Bounded modules

| Module | Responsibility | Current state |
|---|---|---|
| Ingestion | Validate, persist, retrieve, and deduplicate alerts; Grafana webhook adapter | Working vertical slice (webhook path not yet verified against a live lab) |
| Correlation | Group events into incidents using explainable rules | Boundary scaffolded |
| Investigation | Run simulated commands and store evidence | Boundary scaffolded |
| AI analysis | Produce schema-validated, cited hypotheses | Boundary scaffolded |
| Remediation | Policy, approval, Ansible execution, verification, rollback | Boundary scaffolded |
| Simulator | Generate safe, reproducible interface-flap events on random links of the SR Linux lab topology | Working vertical slice |

## Initial deployment

The API and simulator run locally. SQLite provides durable storage with no external service dependency. The persistence interface stays behind the ingestion module so a later PostgreSQL or cloud implementation can be introduced without changing HTTP contracts.

## Core future records

### Incident

- stable incident ID and lifecycle state
- correlation rule and version
- related event IDs
- affected resources and time window
- severity and ownership

### Evidence

- evidence ID, incident ID, collector, and collection time
- exact simulated diagnostic request
- normalized result plus raw output reference
- integrity hash and collection status

### Root-cause hypothesis

- ranked cause and confidence bounded to 0–1
- evidence IDs supporting and contradicting the cause
- alternatives and missing evidence
- recommended next diagnostic step
- model/provider metadata, prompt version, and validation result

### Remediation proposal

- allow-listed action and target scope
- expected effect, blast radius, and risk class
- policy result with rule version
- approval identity and timestamp
- execution idempotency key
- verification and rollback plan

## Safety state machine

```text
PROPOSED -> POLICY_REJECTED
PROPOSED -> AWAITING_APPROVAL -> REJECTED
PROPOSED -> AWAITING_APPROVAL -> APPROVED -> EXECUTING
EXECUTING -> VERIFYING -> SUCCEEDED
EXECUTING -> VERIFYING -> ROLLING_BACK -> ROLLED_BACK
EXECUTING -> FAILED
```

No API or worker may jump directly from `PROPOSED` to `EXECUTING`. Approval expires when proposal inputs, target scope, policy version, or workflow checksum changes.

## Observability plan

The initial slice emits structured request logs, propagates request IDs, exposes health, and reports event counts. Later milestones add OpenTelemetry traces, RED metrics, correlation effectiveness, diagnostic failure rates, AI schema/evidence validation rates, approval latency, execution outcomes, and rollback counts.

## Threat boundaries

- Webhook payloads, diagnostic output, AI output, and playbook variables are untrusted.
- Secrets are referenced by identity or secret-store key, never stored in events or prompts.
- The executor receives a narrow action contract rather than arbitrary shell commands.
- Approval identity must come from authentication, not a user-supplied JSON field.
- Audit storage will be append-only and access-controlled before real execution is enabled.

