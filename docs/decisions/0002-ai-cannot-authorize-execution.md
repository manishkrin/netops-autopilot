# ADR 0002: AI cannot authorize or directly execute remediation

- Status: Accepted
- Date: 2026-10-11

## Context

Model output can be incorrect, manipulated by untrusted diagnostic content, or inconsistent across runs. Network changes can have a large blast radius.

## Decision

AI may summarize evidence, rank hypotheses, and propose actions. Deterministic policy checks and an authenticated human approval are both required before an allow-listed workflow can execute. Any material proposal change invalidates prior approval.

## Consequences

- Model credentials never need network write access.
- Policy and approval become independently testable audit records.
- Some low-risk automation remains slower, by design.
- Autonomous execution is outside the project scope until separately justified and threat-modeled.

