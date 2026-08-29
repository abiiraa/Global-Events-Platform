# Roadmap

> See also: [Architecture](architecture.md) | [Domain Model](domain-model.md) | [DynamoDB Handbook](dynamodb-handbook.md)

## Current Assessment

All four platform modules are fully implemented, tested, and integrated into the unified platform. The system covers the complete fan journey: queue admission → seat purchase → concessions ordering → leaderboard engagement.

## Documentation Foundation — DONE

- Platform README, domain model, architecture, roadmap, and ADRs written.
- Waiting-room design docs (6 documents) complete.
- Module audit against production readiness criteria complete.

## Virtual Waiting Room — DONE

- SAM and NoSQL Workbench projections verified and synced.
- Token validation single-use with conditional write.
- Completion transition decrements `admittedUsers`.
- Capacity-mode pauses promotion (does not destroy queue).
- `batchId` persisted on every admitted fan.
- 150 tests passing (82 unit + 50 integration + 14 API contract + 4 load).

## Fair Seat Purchase — DONE

- Modeled seat, hold, purchase session, ticket, section availability, and fan pointer entities.
- `AVAILABLE → HELD` via conditional write (with expired-hold reclaim).
- `HELD → SOLD` via `TransactWriteItems` verifying holder, session, and fan identity.
- Active release path for holds; TTL as cleanup only.
- Section availability counts updated transactionally inside the purchase transaction.
- Tiered seating model (PREMIUM/STANDARD/GENERAL) with prices.
- Token validation via HTTP call to waiting-room API (clean module boundary).
- Admin venue setup endpoint for seeding stadiums.
- 44 tests passing (26 unit + 18 integration).
- Root SAM stack updated with seat-purchase as nested stack.

## Stadium Concessions Express — DONE

- Single-table design with stands, menus, orders, queue entries, and fan order history.
- FIFO queue via GSI sorted by `{priority}{timestamp}` — VIPs get `0#` prefix, regulars get `1#`.
- Inventory-aware routing: conditionally decrements stock, auto-routes to next-closest stand on failure.
- Order state machine (`PENDING → PREPARING → READY → PICKED_UP`) enforced via conditional writes.
- Inventory rollback on cancellation.
- Admin setup endpoint for seeding concession stands with menus and section coverage.
- Event-wide and per-stand analytics endpoints.
- 8 Lambda handlers with full integration test suite passing.
- Frontend `Concessions.tsx` page with cart, checkout, and live order tracking.

## Infinite Leaderboard — DONE

- 16-shard write model to prevent hot partitions under extreme write concurrency.
- Score inversion (`MAX_SCORE_BASE - score`) for native DynamoDB descending sort.
- Scatter-gather Top-N: reads top items from all 16 shards and merges in memory.
- Exact rank calculation: scatter-gather COUNT query across shards.
- `TransactWriteItems` atomically updates shard entry, participant summary, and profile.
- Participant profile query via GSI1 for "all leaderboards I'm on."
- Global leaderboard listing via GSI2.
- 8 Lambda handlers with full integration test suite passing.
- Frontend `Leaderboard.tsx` page with rankings table and score simulation.

## Production Hardening (Future)

- Cognito authentication and authorization.
- Idempotency keys on all mutation APIs.
- DLQs and replay tooling for EventBridge consumers.
- Observability dashboards and alarms.
- Load tests matching scale targets.
- Cost model per module.
