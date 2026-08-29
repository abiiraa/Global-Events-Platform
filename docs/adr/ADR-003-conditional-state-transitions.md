# ADR-003: Conditional State Transitions

## Status

Accepted.

## Context

The platform models scarce resources: queue admission slots, admission tokens, seats, and tickets. Race conditions would create unfair admission, token replay, or double-selling.

## Decision

Every correctness-sensitive state transition uses DynamoDB condition expressions or transactions.

Examples:

- Join queue uses `attribute_not_exists` in a transaction.
- Admit fan requires `status = WAITING`.
- Validate token requires `status = ACTIVE`.
- Complete admission requires `status = ADMITTED`.
- Seat hold will require `status = AVAILABLE`.
- Seat purchase will require matching hold/session/fan identity.

## Consequences

- Concurrent writers are resolved by DynamoDB, not application timing.
- Failed conditions become expected business conflicts.
- Handler code must distinguish conditional failure from system failure.

