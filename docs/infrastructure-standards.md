# AWS Infrastructure Standards

> See also: [Architecture](architecture.md), [DynamoDB Handbook](dynamodb-handbook.md)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite 8 + TypeScript 6 |
| Styling | Tailwind CSS v4 + shadcn/ui |
| Routing | React Router v7 |
| Server state | TanStack Query v5 |
| Real-time | WebSocket via API Gateway (planned) |
| Auth | Amazon Cognito (planned) |
| Compute | AWS Lambda (Python 3.14) |
| Database | DynamoDB — one table per module |
| Cross-module | EventBridge custom bus (`GlobalSportingEventsBus`) |
| Hosting | AWS Amplify Hosting (planned) |
| IaC | AWS SAM (nested stacks) |
| Linting | oxlint (frontend) |

---

## AWS Service Responsibilities

| Service | Responsibility |
|---------|----------------|
| API Gateway | Public API entry point, routing, auth, rate limiting |
| AWS Lambda | Stateless application logic |
| DynamoDB | Primary operational datastore |
| EventBridge | Domain event routing across modules |
| SQS | Reliable asynchronous processing, DLQ |
| CloudWatch | Logging, metrics, alarms |
| IAM | Authentication and authorization |
| AWS SAM | Infrastructure as Code |

---

## API Gateway Standards

Design APIs around business actions, not CRUD resources:

```
POST /queue/join
POST /purchase/hold
POST /orders
GET  /leaderboards/{id}
```

Business logic must never live in API Gateway.

---

## Lambda Standards

Lambda functions should: have one responsibility, be stateless, be idempotent, fail fast, emit structured logs.

Handler flow:
```
Validate Request → Call Application Layer → Return Response
```

---

## EventBridge Standards

Use EventBridge for domain events crossing module boundaries. Events must be immutable. Use versioned event schemas where practical. Configure SQS DLQs for critical rules.

---

## IAM Principles

Follow least privilege. Each Lambda receives only the permissions it requires. Never use wildcard permissions unless documented and justified.

---

## Infrastructure as Code

All infrastructure is managed through AWS SAM. Avoid manual console changes. Every infrastructure change must be reviewed, version-controlled, and repeatable.

---

## Configuration Management

Never hardcode: ARNs, account IDs, secrets, credentials. Use SAM parameters, environment variables, or Secrets Manager.

---

## Logging Standards

Use structured JSON logs (via SAM `LoggingConfig: LogFormat: JSON`). Every log includes: Correlation ID, Request ID, Event name, Module, Severity. Never log secrets or personal data.

---

## Resilience

Design for: retries, duplicate messages, partial outages, eventual consistency, graceful degradation. Avoid single points of failure.

---

## Deployment Strategy

Preferred flow: Development → Testing → Staging → Production.

Prefer small, reversible deployments. Document breaking infrastructure changes before implementation.
