/**
 * API client for the deployed SAM backend.
 * All functions here map to real Lambda endpoints.
 * Used when VITE_USE_REAL_API=true.
 */

import type { SportingEvent, Ticket } from './types'

const WAITING_ROOM_URL = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ?? ''
const SEAT_PURCHASE_URL = import.meta.env.VITE_SEAT_PURCHASE_API_URL?.replace(/\/$/, '') ?? WAITING_ROOM_URL
const CONCESSIONS_URL = import.meta.env.VITE_CONCESSIONS_API_URL?.replace(/\/$/, '') ?? WAITING_ROOM_URL
const LEADERBOARD_URL = import.meta.env.VITE_LEADERBOARD_API_URL?.replace(/\/$/, '') ?? WAITING_ROOM_URL

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }))
    throw new Error(err.message ?? `HTTP ${res.status}`)
  }
  if (res.status === 204 || res.headers.get('content-length') === '0') {
    return undefined as T
  }
  return res.json()
}

// ── Admin helpers ─────────────────────────────────────────────────────────────

function adminHeaders() {
  return {
    'x-admin-email': import.meta.env.VITE_ADMIN_EMAIL ?? '',
    'x-admin-password': import.meta.env.VITE_ADMIN_PASSWORD ?? '',
  }
}

// ── Events ────────────────────────────────────────────────────────────────────

export async function apiCreateEvent(data: {
  eventId: string
  matchName: string
  stadium: string
  capacity: number
  startTime: string
  status?: string
  imageUrl?: string
  sport?: string
  vipPrice?: number
  premiumPrice?: number
  standardPrice?: number
  economyPrice?: number
}): Promise<void> {
  await apiFetch(`${WAITING_ROOM_URL}/event`, {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify(data),
  })
}

export async function apiGetEvents(): Promise<SportingEvent[]> {
  const data = await apiFetch<{ events: Array<{
    eventId: string
    matchName: string
    stadium: string
    capacity: number
    startTime: string
    status: string
    imageUrl?: string
    sport?: string
    vipPrice?: number
    premiumPrice?: number
    standardPrice?: number
    economyPrice?: number
  }> }>(`${WAITING_ROOM_URL}/events`)

  return data.events.map(e => ({
    id: e.eventId,
    title: e.matchName,
    venue: e.stadium,
    date: e.startTime?.split('T')[0] ?? '',
    time: e.startTime?.split('T')[1]?.slice(0, 5) ?? '',
    sport: e.sport || 'Football',
    imageUrl: e.imageUrl || '',
    totalSeats: e.capacity,
    availableSeats: e.capacity,
    price: e.economyPrice || e.standardPrice || e.premiumPrice || e.vipPrice || 0,
    status: e.status,
    vipPrice: e.vipPrice,
    premiumPrice: e.premiumPrice,
    standardPrice: e.standardPrice,
    economyPrice: e.economyPrice,
  }))
}

export async function apiUpdateEvent(eventId: string, data: {
  matchName?: string
  stadium?: string
  capacity?: number
  startTime?: string
  status?: string
  imageUrl?: string
  sport?: string
  vipPrice?: number
  premiumPrice?: number
  standardPrice?: number
  economyPrice?: number
}): Promise<void> {
  await apiFetch(`${WAITING_ROOM_URL}/event/${encodeURIComponent(eventId)}`, {
    method: 'PUT',
    headers: adminHeaders(),
    body: JSON.stringify(data),
  })
}

export async function apiDeleteEvent(eventId: string): Promise<void> {
  await apiFetch(`${WAITING_ROOM_URL}/event/${encodeURIComponent(eventId)}`, {
    method: 'DELETE',
    headers: adminHeaders(),
  })
}

// ── Queue ─────────────────────────────────────────────────────────────────────

export async function apiJoinQueue(userId: string, eventId: string): Promise<void> {
  await apiFetch(`${WAITING_ROOM_URL}/queue/join`, {
    method: 'POST',
    body: JSON.stringify({ userId, eventId }),
  })
}

export async function apiGetQueueStatus(userId: string, eventId: string): Promise<{
  queuePosition: string | number
  status: string
  estimatedWaitMinutes: number
  tokenId?: string
}> {
  return apiFetch(`${WAITING_ROOM_URL}/queue/status?userId=${encodeURIComponent(userId)}&eventId=${encodeURIComponent(eventId)}`)
}

export async function apiAdmitUsers(eventId: string): Promise<void> {
  await apiFetch(`${WAITING_ROOM_URL}/queue/admit`, {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify({
      eventId,
      batchSize: 100,
      purchasingCapacity: 10000,
      capacityMode: true,
    }),
  })
}

export async function apiGetEventStats(eventId: string): Promise<{
  waitingUsers: number
  admittedUsers: number
  completedUsers: number
  totalUsers: number
  averageWaitMinutes: number
}> {
  return apiFetch(`${WAITING_ROOM_URL}/event/${encodeURIComponent(eventId)}/stats`)
}

export async function apiGetQueueEntries(eventId: string, status = 'WAITING'): Promise<Array<{ userId: string; queuePosition: string; status: string }>> {
  const data = await apiFetch<{ entries: Array<{ userId: string; queuePosition: string; status: string }> }>(
    `${WAITING_ROOM_URL}/queue/admin/list?eventId=${encodeURIComponent(eventId)}&status=${status}&limit=500`,
    { headers: adminHeaders() }
  )
  return data.entries
}

export async function apiLeaveQueueForUser(userId: string, eventId: string): Promise<void> {
  await apiFetch(`${WAITING_ROOM_URL}/queue/leave`, {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify({ userId, eventId }),
  }).catch(() => {})
}

export async function apiLeaveQueue(userId: string, eventId: string): Promise<void> {
  await apiFetch(`${WAITING_ROOM_URL}/queue/leave`, {
    method: 'POST',
    body: JSON.stringify({ userId, eventId }),
  })
}

// ── Seat Purchase ─────────────────────────────────────────────────────────────

export async function apiCreateSession(tokenId: string, eventId: string): Promise<{ sessionId: string }> {
  return apiFetch(`${SEAT_PURCHASE_URL}/purchase/session`, {
    method: 'POST',
    body: JSON.stringify({ tokenId, eventId }),
  })
}

export async function apiGetSeatMap(eventId: string, sectionId: string): Promise<{ seats: unknown[] }> {
  return apiFetch(`${SEAT_PURCHASE_URL}/purchase/seats/${encodeURIComponent(eventId)}/${encodeURIComponent(sectionId)}`)
}

export async function apiHoldSeat(sessionId: string, eventId: string, sectionId: string, seatLabel: string): Promise<{ holdId: string }> {
  return apiFetch(`${SEAT_PURCHASE_URL}/purchase/hold`, {
    method: 'POST',
    body: JSON.stringify({ sessionId, eventId, sectionId, seatLabel }),
  })
}

export async function apiSetupVenue(eventId: string, sections: Array<{
  sectionId: string
  tier: string
  price: number
  seats: string[]
}>): Promise<void> {
  await apiFetch(`${SEAT_PURCHASE_URL}/admin/venue/setup`, {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify({ eventId, sections }),
  })
}

export async function apiConfirmPurchase(sessionId: string, holdId: string): Promise<{ ticketId: string }> {
  return apiFetch(`${SEAT_PURCHASE_URL}/purchase/confirm`, {
    method: 'POST',
    body: JSON.stringify({ sessionId, holdId }),
  })
}

export async function apiGetTickets(fanId: string): Promise<Ticket[]> {
  const data = await apiFetch<{ tickets: Array<{
    ticketId: string
    eventId: string
    fanId: string
    sectionId: string
    seatLabel: string
    tier: string
    price: number
    purchasedAt: string
  }> }>(`${SEAT_PURCHASE_URL}/purchase/tickets/${encodeURIComponent(fanId)}`)

  return data.tickets.map(t => ({
    id: t.ticketId,
    eventId: t.eventId,
    userId: t.fanId,
    section: t.sectionId,
    row: t.seatLabel?.split('-')[0] ?? 'A',
    seat: parseInt(t.seatLabel?.split('-')[1] ?? '1'),
    tier: t.tier,
    price: t.price,
    purchasedAt: t.purchasedAt,
  }))
}

// ── Concessions ─────────────────────────────────────────────────────────────

export async function apiPlaceOrder(data: {
  eventId: string
  fanId: string
  section: string
  items: Array<{ itemId: string; name: string; quantity: number; price: number }>
  isVip?: boolean
}): Promise<{ orderId: string; standId: string; status: string; totalPrice: number }> {
  return apiFetch(`${CONCESSIONS_URL}/concessions/order`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function apiGetOrderStatus(orderId: string): Promise<{
  orderId: string
  status: string
  standId: string
  standName: string
  items: Array<any>
  totalPrice: number
  orderTime: string
}> {
  return apiFetch(`${CONCESSIONS_URL}/concessions/order/${encodeURIComponent(orderId)}`)
}

export async function apiGetFanOrders(fanId: string, eventId: string): Promise<{ orders: any[]; count: number }> {
  return apiFetch(`${CONCESSIONS_URL}/concessions/orders/${encodeURIComponent(fanId)}?eventId=${encodeURIComponent(eventId)}`)
}

// ── Leaderboard ─────────────────────────────────────────────────────────────

export async function apiSubmitScore(data: {
  leaderboardId: string
  participantId: string
  participantName: string
  score: number
  scoreData?: Record<string, any>
}): Promise<{ score: number; previousScore: number | null }> {
  return apiFetch(`${LEADERBOARD_URL}/leaderboard/score`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function apiGetTopN(leaderboardId: string, limit = 10): Promise<{ rankings: any[] }> {
  return apiFetch(`${LEADERBOARD_URL}/leaderboard/${encodeURIComponent(leaderboardId)}/top?limit=${limit}`)
}

export async function apiGetParticipantProfile(participantId: string): Promise<{
  participantName: string
  leaderboards: any[]
  totalLeaderboards: number
}> {
  return apiFetch(`${LEADERBOARD_URL}/leaderboard/participant/${encodeURIComponent(participantId)}`)
}

export async function apiSetupStands(eventId: string): Promise<void> {
  const defaultStands = [
    {
      standId: `stand-main-${eventId}`,
      standName: "Main Concourse Stand",
      coveredSections: ["VIP", "PREMIUM", "STANDARD", "ECONOMY"],
      menu: [
        { itemId: "nachos", itemName: "Loaded Nachos", price: 12, inventory: 10000 },
        { itemId: "hotdog", itemName: "Stadium Hot Dog", price: 8, inventory: 10000 },
        { itemId: "pretzel", itemName: "Soft Pretzel", price: 6, inventory: 10000 },
        { itemId: "beer", itemName: "Draft Beer", price: 10, inventory: 10000 },
        { itemId: "soda", itemName: "Fountain Soda", price: 5, inventory: 10000 }
      ]
    }
  ]
  await apiFetch(`${CONCESSIONS_URL}/concessions/admin/stands/setup`, {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify({ eventId, stands: defaultStands })
  })
}

export async function apiCreateLeaderboard(leaderboardId: string, name: string): Promise<void> {
  await apiFetch(`${LEADERBOARD_URL}/leaderboard/create`, {
    method: 'POST',
    headers: adminHeaders(),
    body: JSON.stringify({ leaderboardId, name, type: 'FAN_ENGAGEMENT' })
  })
}

