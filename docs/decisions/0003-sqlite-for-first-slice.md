# ADR 0003: Use SQLite for the first slice

- Status: Accepted
- Date: 2026-10-11

## Context

Month one needs durable, queryable storage and idempotency without requiring cloud accounts or container dependencies.

## Decision

Use SQLite behind a small store class. Use the external `event_id` as the primary key and `INSERT OR IGNORE` to make webhook retries safe.

## Consequences

- The demo works from a clean local checkout.
- SQLite is not presented as the final high-scale architecture.
- Concurrent-load limitations will be measured before choosing PostgreSQL, DynamoDB, or another store.

