# ADR-004: TTL Is Cleanup, Not Business Timing

## Status

Accepted.

## Context

Admission tokens, purchase sessions, and seat holds expire. DynamoDB TTL is useful for deleting old items, but deletion is eventually consistent and may occur after the nominal expiry time.

## Decision

Use TTL for cleanup only. Business logic must check explicit expiry attributes such as `expiresAt` or `holdExpiresAt` before accepting a token, hold, or session.

## Consequences

- Expired records may remain in the table temporarily.
- Validation remains correct because code checks expiry time.
- The Seat Purchase module needs an active hold-release path so expired seats become available quickly.

