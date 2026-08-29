# GSEP Frontend

React SPA for the Global Sporting Event Platform.

## Stack

- React 19 + Vite 8 + TypeScript 6
- Tailwind CSS v4 (CSS-first config)
- React Router (client-side routing)
- localStorage auth (Cognito planned)

## Quick Start

```bash
npm install
npm run dev     # http://localhost:5173
npm run build   # Production build
npm run lint    # Oxlint check
```

## Source Structure

```
src/
├── App.tsx                  # Root component with RouterProvider
├── main.tsx                 # Entry point
├── index.css                # Tailwind directives + scroll-reveal animation
├── router.tsx               # Route definitions
├── context/AuthContext.tsx   # Auth provider (localStorage + loading state)
├── layouts/AppLayout.tsx    # Authenticated shell (sidebar + header)
├── pages/
│   ├── Landing.tsx          # Full-page hero, stats, features, FAQ, CTA
│   ├── Login.tsx            # Email/password + Google OAuth button
│   ├── Signup.tsx           # Registration + Google OAuth button
│   ├── Dashboard.tsx        # Event cards, registration flow
│   ├── WaitingRoom.tsx      # User-based queue position
│   ├── SeatPurchase.tsx     # Section selection + tier pricing
│   ├── MyMatches.tsx        # Purchased tickets only
│   └── MatchDetail.tsx      # Ticket info + future modules
└── lib/
    ├── store.ts             # Events, registrations, tickets, queue (localStorage)
    ├── types.ts             # Shared TypeScript interfaces
    └── utils.ts             # cn() helper
```

## Design

Blue/black dark theme with geometric elements. See [DESIGN-DOC.md](DESIGN-DOC.md) for full design tokens and layout structure.

## Scaling

See [SCALING-GUIDE.md](SCALING-GUIDE.md) for adding sports, ticket providers, Stripe payments, and Google OAuth.
