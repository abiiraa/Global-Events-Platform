# DynamoDB Engineering Handbook

> See also: [Architecture](architecture.md), [ADRs](adr/)

---

## Philosophy

Business Problem → Domain Model → State Machine → Events → Access Patterns → DynamoDB.

Never reverse this order. If a schema cannot be justified by an access pattern, redesign it.

---

## Access Pattern First Design

Every item stored in DynamoDB must answer a question. Never create attributes "for future use." Document every access pattern before implementing the schema.

---

## Single Table Strategy

One table per bounded context (module) is this platform's default.

Single Table Design minimizes round trips and supports multiple entity types — but do not force unrelated entities into one table if it harms clarity or scalability.

---

## Primary Key Design

Partition Keys should: distribute writes evenly, avoid hot partitions, reflect ownership boundaries.

Sort Keys should: represent hierarchy, enable range queries, support entity composition.

Naming conventions:
```
PK = EVENT#{eventId}
SK = FAN#{fanId}
```

---

## Global Secondary Indexes

Every GSI requires documentation covering: business purpose, access pattern, PK, SK, expected read volume, expected write amplification.

If these cannot be explained, do not create the index.

---

## Hot Partition Avoidance

Warning signs: sequential identifiers, timestamp-only PK, single event receiving all writes, global counters.

Mitigation: write sharding, random suffixes, hash buckets, time windows, event partitioning.

---

## Conditional Writes

Use conditional expressions whenever correctness matters.

- Waiting Room: only promote fans currently WAITING.
- Ticketing: only hold seats that are AVAILABLE.
- Leaderboards: prevent stale score updates when ordering matters.

Conditional writes are preferred over read-modify-write patterns.

---

## Transactions

Use DynamoDB Transactions only when atomicity is required (seat hold + purchase session, purchase confirmation, inventory ownership transfer). Keep transactions as small as possible.

---

## TTL

Use TTL for temporary entities only (seat holds, admission tokens, purchase sessions, queue sessions).

Do not rely on TTL for precise business timing. Critical expiration logic should be implemented explicitly.

---

## Consistency

- Eventually Consistent Reads: queue polling, leaderboards, statistics, browsing.
- Strongly Consistent Reads: use only when correctness requires immediate visibility. Document every strong read.

---

## Idempotency

Assume duplicate requests occur. Operations should safely retry.

- Join Queue: repeated requests must not create duplicate queue entries.
- Seat Hold: retries must not create duplicate reservations.
- Purchase Confirmation: duplicate payment callbacks must not duplicate tickets.

---

## Scan Policy

Scans are prohibited in production paths unless explicitly justified.

Preferred order: Query → BatchGet → Transaction → Scan (last resort, never for user-facing operations).

---

## Review Checklist

Before approving schema changes ask:

- Which access pattern requires this?
- Can it scale to millions?
- Will it create hot partitions?
- Is the partition key well distributed?
- Does every GSI have a documented purpose?
- Are conditional writes used where required?
- Is TTL appropriate?
- Is eventual consistency acceptable?
- Is denormalization justified?

---

## Anti-Patterns

Avoid: designing tables before access patterns, generic CRUD schemas, sequential hot PK, unnecessary GSIs, full table scans, large transactions, hidden state transitions, business logic inside persistence adapters.
