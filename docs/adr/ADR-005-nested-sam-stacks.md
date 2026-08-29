# ADR-005: Nested SAM Stacks

## Status

Accepted.

## Context

The project is a platform composed of multiple independently deployable modules. It needs one-command platform deployment while preserving module independence.

## Decision

Use a root SAM template that defines shared infrastructure and nests module SAM templates.

## Consequences

- The waiting-room module can deploy independently.
- The root stack can wire modules together through shared outputs such as EventBridge bus ARN.
- New modules can be added without rewriting existing module infrastructure.

