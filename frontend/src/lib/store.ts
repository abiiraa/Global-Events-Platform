import type { Ticket, SportingEvent } from './types'
import {
  apiGetEvents,
  apiJoinQueue,
  apiGetQueueStatus,
  apiGetTickets,
} from './api'

const TICKETS_KEY = 'gsep_tickets'
const REGISTRATIONS_KEY = 'gsep_registrations'
const EVENTS_KEY = 'gsep_events'

const USE_REAL_API = import.meta.env.VITE_USE_REAL_API === 'true'

const DEFAULT_EVENTS: SportingEvent[] = [
  {
    id: 'evt_001',
    title: 'UEFA Champions League Final',
    venue: 'Wembley Stadium, London',
    date: '2026-08-15',
    time: '20:00',
    sport: 'Football',
    imageUrl: 'https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=800&q=80',
    totalSeats: 90000,
    availableSeats: 12450,
    price: 250,
  },
  {
    id: 'evt_002',
    title: 'The Masters Tournament',
    venue: 'Augusta National Golf Club',
    date: '2026-09-10',
    time: '08:00',
    sport: 'Golf',
    imageUrl: 'https://images.unsplash.com/photo-1535131749006-b7f58c99034b?w=800&q=80',
    totalSeats: 40000,
    availableSeats: 8200,
    price: 175,
  },
  {
    id: 'evt_003',
    title: 'Wimbledon Mens Final',
    venue: 'All England Club, London',
    date: '2026-07-12',
    time: '14:00',
    sport: 'Tennis',
    imageUrl: 'https://images.unsplash.com/photo-1554068865-24cecd4e34b8?w=800&q=80',
    totalSeats: 15000,
    availableSeats: 3100,
    price: 320,
  },
  {
    id: 'evt_004',
    title: 'NBA Finals Game 7',
    venue: 'Madison Square Garden, NYC',
    date: '2026-06-20',
    time: '21:00',
    sport: 'Basketball',
    imageUrl: 'https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800&q=80',
    totalSeats: 20000,
    availableSeats: 1580,
    price: 450,
  },
  {
    id: 'evt_005',
    title: 'Formula 1 Monaco Grand Prix',
    venue: 'Circuit de Monaco',
    date: '2026-05-24',
    time: '15:00',
    sport: 'Motorsport',
    imageUrl: 'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800&q=80',
    totalSeats: 37000,
    availableSeats: 5600,
    price: 380,
  },
]

// ── Local event CRUD (admin portal, localStorage) ─────────────────────────────

export function getEvents(): SportingEvent[] {
  const raw = localStorage.getItem(EVENTS_KEY)
  return raw ? JSON.parse(raw) : DEFAULT_EVENTS
}

export function saveEvents(events: SportingEvent[]): void {
  localStorage.setItem(EVENTS_KEY, JSON.stringify(events))
}

export function addEvent(event: SportingEvent): void {
  saveEvents([...getEvents(), event])
}

export function updateEvent(updated: SportingEvent): void {
  saveEvents(getEvents().map(e => (e.id === updated.id ? updated : e)))
}

export function deleteEvent(eventId: string): void {
  saveEvents(getEvents().filter(e => e.id !== eventId))
}

// Legacy constant — pages that need a sync snapshot use this
export const EVENTS: SportingEvent[] = getEvents()

// ── Async events (API or localStorage) ───────────────────────────────────────

export async function fetchEvents(): Promise<SportingEvent[]> {
  if (USE_REAL_API) return apiGetEvents()
  return getEvents()
}

// ── Tickets ───────────────────────────────────────────────────────────────────

export function getTickets(userId: string): Ticket[] {
  const raw = localStorage.getItem(TICKETS_KEY)
  const all: Ticket[] = raw ? JSON.parse(raw) : []
  return all.filter(t => t.userId === userId)
}

export function addTicket(ticket: Ticket): void {
  const raw = localStorage.getItem(TICKETS_KEY)
  const all: Ticket[] = raw ? JSON.parse(raw) : []
  all.push(ticket)
  localStorage.setItem(TICKETS_KEY, JSON.stringify(all))
}

export async function fetchTickets(userId: string): Promise<Ticket[]> {
  if (USE_REAL_API) return apiGetTickets(userId)
  return getTickets(userId)
}

// ── Registrations / queue (localStorage) ─────────────────────────────────────

export function getRegistrations(userId: string): string[] {
  const raw = localStorage.getItem(REGISTRATIONS_KEY)
  const all: Record<string, string[]> = raw ? JSON.parse(raw) : {}
  return all[userId] || []
}

export function registerForEventLocal(userId: string, eventId: string): void {
  const raw = localStorage.getItem(REGISTRATIONS_KEY)
  const all: Record<string, string[]> = raw ? JSON.parse(raw) : {}
  if (!all[userId]) all[userId] = []
  if (!all[userId].includes(eventId)) all[userId].push(eventId)
  localStorage.setItem(REGISTRATIONS_KEY, JSON.stringify(all))
}

export async function registerForEvent(userId: string, eventId: string): Promise<void> {
  if (USE_REAL_API) {
    await apiJoinQueue(userId, eventId)
  }
  // Always mirror locally so UI is instant
  registerForEventLocal(userId, eventId)
}

export function isRegistered(userId: string, eventId: string): boolean {
  return getRegistrations(userId).includes(eventId)
}

export function getQueuePosition(userId: string, eventId: string): number {
  const raw = localStorage.getItem(REGISTRATIONS_KEY)
  const all: Record<string, string[]> = raw ? JSON.parse(raw) : {}
  let position = 1
  for (const [uid, events] of Object.entries(all)) {
    if (uid === userId) break
    if (events.includes(eventId)) position++
  }
  return Math.max(position * 12 + Math.floor(userId.charCodeAt(4) % 30), 5)
}

export async function fetchQueueStatus(userId: string, eventId: string): Promise<{
  queuePosition: string | number
  status: string
  estimatedWaitMinutes: number
  tokenId?: string
}> {
  if (USE_REAL_API) return apiGetQueueStatus(userId, eventId)
  const pos = getQueuePosition(userId, eventId)
  return {
    queuePosition: pos,
    status: 'WAITING',
    estimatedWaitMinutes: Math.ceil(pos / 20),
  }
}
