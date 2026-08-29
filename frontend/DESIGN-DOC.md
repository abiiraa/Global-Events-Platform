# GSEP Frontend — Design Document

Blue/black dark theme with geometric elements, purpose-built for a high-traffic sporting event platform.

---

## Design Tokens

### Colors
| Role | Hex | Usage |
|------|-----|-------|
| Background | `#010101` | Page background |
| Surface | `#0a0a0a` | Card backgrounds, nav |
| Border | `rgba(255,255,255,0.06)` | Subtle borders |
| Accent Primary | `#3b82f6` (blue-500) | CTAs, highlights, active states |
| Accent Glow | `#60a5fa` (blue-400) | Hover glow, text gradients |
| Accent Secondary | `#1d4ed8` (blue-700) | Darker accent for depth |
| Text Primary | `#ffffff` | Headlines |
| Text Secondary | `rgba(255,255,255,0.5)` | Body text |
| Text Muted | `rgba(255,255,255,0.25)` | Labels, metadata |

### Typography
- **Display**: Space Grotesk 700 — hero headlines (clamp 3rem–6rem)
- **Body**: Outfit 400/500 — paragraphs, nav
- **Mono**: JetBrains Mono — stats, code-like elements

### Spacing
- Section padding: `py-24 md:py-32`
- Container: `max-w-7xl mx-auto px-6`
- Card gap: `gap-6`

---

## Layout Structure (Sections in order)

### 1. Navigation (Fixed)
- Glass-morphism bar with subtle angular border via CSS clip-path
- Logo (GSEP) left, nav links center, CTA button right
- Button has angular/clipped corners (CSS clip-path polygon)
- Sticky with backdrop-blur on scroll

### 2. Hero Section
- Full viewport height
- Large headline in bold white
- Subtitle: single line describing the platform
- CTA button with blue fill + angular clip-path shape
- Stats row: `10M+` fans, `<50ms` latency, `0` double-sells
- Background: subtle radial gradient + grid overlay pattern

### 3. Stats Bar
- Horizontal row of 3 large stat numbers with blue accent
- Separated by thin vertical lines

### 4. Solutions Section
- Section heading centered
- Alternating rows of feature cards (left text / right visual, then flipped)
- Features: Fair Queuing, Instant Tickets, Stadium Concessions, Live Leaderboard

### 5. Key Features Grid
- 3-column grid of icon + title + short description cards
- Icons in blue-tinted circles

### 6. Big Typography Section
- Full-width statement in massive type
- Subtle text gradient or white

### 7. Technology Stack
- AWS service badges in a row
- DynamoDB, Lambda, EventBridge, API Gateway, SQS

### 8. FAQ Accordion
- Dark cards with border, click to expand/collapse
- Blue accent on active item

### 9. CTA Footer + Footer
- Headline + CTA button, background gradient glow
- Logo, links, copyright

---

## Geometric Design Elements

1. **Angular buttons**: CSS `clip-path: polygon(...)` — sci-fi cut corners
2. **Card borders**: 1px `rgba(255,255,255,0.06)` with rounded corners
3. **Glow effects**: `box-shadow: 0 0 60px rgba(59,130,246,0.15)` on hover
4. **Grid overlay**: Repeating thin lines as background pattern
5. **Scroll reveal**: Elements fade up on viewport enter (IntersectionObserver + `.reveal-on-scroll` / `.revealed` CSS classes in `index.css`)

---

## Functional Design Decisions

1. **Auth loading state** — `AuthContext` starts `loading: true`, sets to `false` after localStorage restore. Prevents AppLayout redirecting to `/login` on page refresh before session is read.
2. **Queue position** — calculated from user registration order in localStorage (not random). See `getQueuePosition()` in `store.ts`.
3. **My Matches** — only shows events with purchased tickets (calls `getTickets()`). No "register but no ticket" entries.
4. **Admin events** — all fan pages call `getEvents()` at render time (not a static constant) so admin-created/edited events are immediately visible.
5. **No pitch box** — SeatPurchase page uses section selection buttons only. The stadium SVG visualisation was removed.

---

## Implementation Priority (completed)

1. Landing page (blue/black dark design)
2. My Matches logic (tickets only)
3. Remove pitch box from SeatPurchase
4. Connect queue to registration order
5. Google Auth button (UI scaffolded — needs `@react-oauth/google` + credentials)
6. Payment gateway (documented in `SCALING-GUIDE.md`)
7. Admin Portal (`/admin`) — full event CRUD
