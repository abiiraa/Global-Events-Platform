# ADR-002: Waiting Room Write Sharding

## Status

Accepted.

## Context

The waiting room must absorb millions of near-simultaneous fan arrivals for the same event. If every queue entry used `PK=EVENT#{eventId}`, the event partition would become a hot partition.

## Decision

Store queue entries under 16 deterministic event shards:

```text
PK = EVENT#{eventId}#SHARD#{00-15}
SK = QUEUE#{queuePosition}
```

The shard is derived from a stable hash of event and fan identity.

## Consequences

- Burst writes are distributed across multiple partitions.
- Fan status remains cheap because the registration guard stores the exact queue item key.
- Admission requires querying each shard and merging by queue position in Lambda.
- The shard count is a deliberate cost/performance trade-off and should not change casually.

