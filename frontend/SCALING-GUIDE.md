# Scaling Guide: Adding Sports & Ticket Providers

## Overview

This document explains how to scale the Global Sporting Event Platform to support multiple sports, venues, and third-party ticket providers.

---

## 1. Adding New Sports Events

### Data Model

Each event is defined in `src/lib/store.ts` as a `SportingEvent`:

```typescript
interface SportingEvent {
  id: string          // Unique ID (evt_001, evt_002, etc.)
  title: string       // Event name
  venue: string       // Venue name + city
  date: string        // ISO date (YYYY-MM-DD)
  time: string        // 24h time (HH:MM)
  sport: string       // Sport category (Football, Tennis, etc.)
  imageUrl: string    // Cover image URL
  totalSeats: number  // Venue capacity
  availableSeats: number
  price: number       // Starting price
}
```

### Steps to Add Events

1. Add new entries to the `EVENTS` array in `src/lib/store.ts`
2. Use Unsplash or your own CDN for event images
3. The Dashboard will automatically render them

### Supported Sports Categories

Add any sport string — the UI displays it as a badge on event cards. Common ones:
- Football, Tennis, Golf, Basketball, Motorsport
- Cricket, Rugby, Baseball, Boxing, Swimming, Athletics

---

## 2. Connecting to Real Ticket Providers

### Architecture for Provider Integration

Replace `src/lib/store.ts` with API calls to your backend:

```
Frontend (TanStack Query) → API Gateway → Lambda → DynamoDB
                                        ↓
                              Provider Adapters (Ticketmaster, StubHub, etc.)
```

### Provider Adapter Pattern

Create adapters in the backend for each provider:

```python
# backend/modules/seat-purchase/adapters/ticketmaster.py
class TicketmasterAdapter:
    def search_events(self, sport: str, date_range: tuple) -> list[Event]:
        # Call Ticketmaster Discovery API
        pass
    
    def get_availability(self, event_id: str) -> list[Section]:
        # Call Ticketmaster Inventory API
        pass
    
    def hold_seat(self, event_id: str, seat_id: str, session_id: str) -> HoldResult:
        # Call Ticketmaster Commerce API
        pass
```

### Supported Providers (Integration Templates)

| Provider | API | Use Case |
|----------|-----|----------|
| Ticketmaster | Discovery + Commerce API | Major sports & concerts |
| StubHub | Catalog + Inventory API | Secondary market |
| SeatGeek | Platform API | Multi-sport aggregation |
| Eventbrite | REST API v3 | Smaller events |
| Custom venues | Direct DynamoDB | Own inventory |

---

## 3. Multi-Tenant Deployment

### Per-Sport Branding

Add a `brand` field to events or create sport-specific themes:

```typescript
const SPORT_THEMES: Record<string, { accent: string; gradient: string }> = {
  Football: { accent: '#22c55e', gradient: 'from-green-500 to-emerald-600' },
  Tennis:   { accent: '#eab308', gradient: 'from-yellow-500 to-amber-600' },
  F1:       { accent: '#ef4444', gradient: 'from-red-500 to-red-700' },
}
```

### White-Label Mode

Deploy separate instances per organization:
1. Environment variable `GSEP_TENANT=premier-league`
2. Tenant config loaded at build time (logo, colors, providers)
3. Same codebase, different branding

---

## 4. Payment Gateway Integration

### Stripe (Recommended)

```bash
npm install @stripe/stripe-js @stripe/react-stripe-js
```

#### Frontend Flow

1. User selects seat → frontend creates a `PaymentIntent` via your API
2. Display Stripe Elements (card input)
3. On success → call `addTicket()` and redirect to My Matches

```typescript
// src/lib/payment.ts
import { loadStripe } from '@stripe/stripe-js'

const stripe = await loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY)

export async function createCheckoutSession(ticketData: TicketRequest) {
  const response = await fetch('/api/create-payment-intent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ticketData),
  })
  return response.json()
}
```

#### Backend Lambda

```python
import stripe

def handler(event, context):
    body = json.loads(event['body'])
    intent = stripe.PaymentIntent.create(
        amount=body['price'] * 100,  # cents
        currency='usd',
        metadata={'event_id': body['eventId'], 'seat_id': body['seatId']}
    )
    return {'statusCode': 200, 'body': json.dumps({'clientSecret': intent.client_secret})}
```

### Environment Variables

```env
VITE_STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...        # Backend only
VITE_GOOGLE_CLIENT_ID=...google...   # For Google OAuth
```

---

## 5. Google OAuth Integration

### Setup

1. Create OAuth 2.0 credentials in Google Cloud Console
2. Add authorized redirect URIs for your domain
3. Install: `npm install @react-oauth/google`

### Implementation

```typescript
// src/main.tsx
import { GoogleOAuthProvider } from '@react-oauth/google'

<GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
  <App />
</GoogleOAuthProvider>
```

```typescript
// In Login/Signup page
import { GoogleLogin } from '@react-oauth/google'

<GoogleLogin
  onSuccess={(response) => {
    // Decode JWT, create/find user, set session
    const decoded = jwtDecode(response.credential)
    authContext.loginWithGoogle(decoded.email, decoded.name)
  }}
/>
```

---

## 6. Scaling the Backend

### DynamoDB Capacity

- Use on-demand mode for unpredictable traffic spikes (event launches)
- Switch to provisioned + auto-scaling for steady-state
- Each module has its own table — scale independently

### Lambda Concurrency

- Set reserved concurrency for critical paths (seat holds)
- Use provisioned concurrency for sub-50ms cold starts during launches

### EventBridge Throughput

- Default: 10,000 events/second per bus
- Request quota increase for major events
- Use SQS DLQ for guaranteed processing

### CDN & Static Assets

- Deploy frontend to CloudFront
- Use S3 for event images
- Cache aggressively (event data changes infrequently)

---

## 7. Monitoring & Observability

- CloudWatch dashboards per module
- X-Ray tracing for latency debugging
- Custom metrics: queue depth, seat hold rate, purchase conversion
- Alerting on: double-sell attempts (should be 0), queue starvation, payment failures

---

## Quick Start: Add a New Sport

```bash
# 1. Add events to the store
# 2. Build and deploy
cd frontend && npm run build
cd backend && sam deploy

# 3. Verify
# - New events appear on Dashboard
# - Registration → Queue → Purchase flow works
# - Tickets appear in My Matches
```
