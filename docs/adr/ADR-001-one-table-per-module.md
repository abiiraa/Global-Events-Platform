# ADR-001: One DynamoDB Table Per Module

## Status

Accepted.

## Context

The platform contains four bounded contexts. A single platform-wide DynamoDB table would make cross-module modeling possible, but it would blur ownership and make each module harder to develop and test independently.

## Decision

Use one DynamoDB table per module. Inside each module, use single-table design for that module's entities and access patterns.

## Consequences

- Each module can be developed, tested, and deployed independently.
- Module key schemas can evolve without forcing unrelated modules to migrate.
- Cross-module workflows use events or APIs instead of direct table access.
- Some data is duplicated across modules as event-driven projections.

