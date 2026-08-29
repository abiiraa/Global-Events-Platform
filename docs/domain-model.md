# Domain Model

> See also: [Architecture](architecture.md) | [DynamoDB Handbook](dynamodb-handbook.md)

This platform models the digital flow around a global sporting event: fans arrive, wait, buy seats, order concessions, and participate in engagement experiences.

## Bounded Contexts

| Context | Owns | Must Not Own |
|---|---|---|
| Waiting Room | Queue entries, admission, fairness, admission tokens | Seats, payments, food orders, rankings |
| Seat Purchase | Venue inventory, holds, purchase sessions, tickets | Queue ordering, concessions, ranking calculations |
| Concessions | Menus, stands, order routing, fulfillment state | Ticket ownership, queue admission |
| Leaderboard | Score events, fan score summaries, ranking views | Orders, tickets, queue states |

## Core Entities

| Entity | Meaning |
|---|---|
| Fan | A user participating in one or more event experiences |
| Event | A sporting event with its own queue, ticket inventory, concessions, and leaderboards |
| Venue | Physical stadium layout, sections, rows, seats, and concession stands |
| Queue Entry | A fan's place in the waiting room for one event |
| Admission Token | A short-lived, single-use credential allowing a fan into purchase flow |
| Purchase Session | A time-limited ticket-buying session created after admission |
| Seat | A specific venue seat with availability state |
| Seat Hold | Temporary exclusive claim on one seat for one fan/session |
| Ticket | Confirmed ownership of a sold seat |
| Concession Order | Food or beverage request tied to a fan, seat, and stand |
| Score Event | Immutable fact used to update a leaderboard |

## State Ownership

Waiting room states:

```text
WAITING -> ADMITTED -> COMPLETED
WAITING -> CANCELLED
WAITING -> REGISTRATION_CLOSED
TOKEN ACTIVE -> USED
TOKEN ACTIVE -> EXPIRED
```

Seat purchase states:

```text
SEAT AVAILABLE -> HELD -> SOLD
SEAT HELD -> AVAILABLE
PURCHASE_SESSION CREATED -> ACTIVE -> COMPLETED
PURCHASE_SESSION ACTIVE -> EXPIRED
```

Concessions states:

```text
PENDING -> PREPARING -> READY -> PICKED_UP
PENDING -> CANCELLED
```

Leaderboard score events use `TransactWriteItems` to atomically update the shard entry, participant summary, and profile. Rankings are derived projections via scatter-gather queries.

## Cross-Context Events

| Event | Producer | Consumers | Purpose |
|---|---|---|---|
| `FanAdmitted` | Waiting Room | Seat Purchase | Create or allow a purchase session |
| `TicketPurchased` | Seat Purchase | Waiting Room, Concessions, Leaderboard | Complete queue admission, unlock fan services, update engagement |
| `OrderPlaced` | Concessions | Leaderboard | Increase engagement score |
| `ScoreUpdated` | Leaderboard | Future notification/reporting flows | Publish score/ranking activity |

## Platform Invariants

- A fan has at most one active queue entry per event.
- Queue admission respects the deterministic queue order within the documented fairness model.
- An admission token is single-use and event-specific.
- A seat cannot be held by two fans at the same time.
- A seat cannot be sold twice.
- A completed ticket purchase is immutable unless a future refund workflow exists.
- Order fulfillment transitions are monotonic.
- Score writes are immutable facts; summaries and rankings are projections.

