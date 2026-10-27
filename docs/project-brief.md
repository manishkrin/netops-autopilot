# Project brief

## Purpose

NetOps Autopilot demonstrates a complete, trustworthy network-operations lifecycle: accept noisy alerts, turn them into incidents, investigate using reproducible diagnostics, explain likely causes with evidence and uncertainty, and execute only approved, policy-compliant automation.

It is a six-month flagship portfolio project that combines network operations, Python, cloud architecture, Ansible, AI engineering, testing, and operational leadership in one coherent product.

## Reference scenario

A simulated router experiences interface flapping and emits 25 alerts. The platform deduplicates and correlates them into one incident, retrieves simulated interface history and topology, identifies a likely physical-link fault, proposes safe diagnostics or remediation, asks for approval, runs an idempotent Ansible workflow, verifies the result, and records every decision and action.

## Product capabilities

1. Ingest network alerts through authenticated webhooks and a safe simulator.
2. Persist the original event and reject or identify duplicate deliveries without double processing.
3. Correlate events into incidents using transparent, testable rules before considering ML.
4. Run simulated network diagnostics and store immutable, timestamped evidence.
5. Generate structured root-cause hypotheses that cite evidence, state confidence, list alternatives, and identify missing information.
6. Propose remediation without directly changing infrastructure.
7. Evaluate deterministic safety policy, require explicit human approval, and separate approval from execution.
8. Execute allow-listed Ansible workflows with idempotency keys, bounded credentials, verification, timeout handling, and rollback paths.
9. Record append-only audit events across the entire incident lifecycle.
10. Provide tests, CI, observability, infrastructure as code, load tests, and published benchmark evidence.

## Success measures

- A reviewer can run a five-minute local demonstration from a clean checkout.
- One thousand synthetic events are accepted reliably and measured, not merely claimed.
- Duplicate alerts do not create duplicate events or remediation runs.
- Every hypothesis points to evidence and communicates uncertainty.
- No remediation can execute without a passing policy result and a recorded human approval.
- A failed or ineffective change has a documented verification and rollback route.
- CI proves core behavior and documentation explains important trade-offs.

## Guardrails

- Use no proprietary employer code, data, device configurations, credentials, incidents, or customer information.
- Use only synthetic devices and lab-safe execution targets until an operator deliberately configures an authorized lab.
- Never give an LLM network credentials or a direct unrestricted execution path.
- Treat AI output as untrusted input to deterministic validation.
- Prefer one deployable service and one database until measured requirements justify distribution.

## Deliberate non-goals for the first milestones

- A frontend
- A multi-agent orchestration framework
- Elaborate retrieval-augmented generation
- Dozens of microservices
- Unsupervised changes to real devices
- Claims of scale without benchmark data
