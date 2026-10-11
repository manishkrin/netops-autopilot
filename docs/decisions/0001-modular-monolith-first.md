# ADR 0001: Start with a modular monolith

- Status: Accepted
- Date: 2026-10-11

## Context

The target system has distinct ingestion, correlation, investigation, analysis, and remediation responsibilities. Premature services would introduce deployment, messaging, consistency, and observability work before the domain behavior is proven.

## Decision

Build one deployable Python API with explicit package boundaries and a local SQLite store. Keep domain contracts independent enough to replace persistence or extract a worker later.

## Consequences

- Local development and demonstrations stay simple.
- Cross-module changes can remain atomic while the model evolves.
- Scale claims must come from measurements.
- Extraction is deferred until throughput, fault isolation, ownership, or deployment evidence justifies it.

