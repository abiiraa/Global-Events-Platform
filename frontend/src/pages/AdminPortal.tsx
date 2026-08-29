import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { apiGetEvents, apiCreateEvent, apiUpdateEvent, apiDeleteEvent, apiGetEventStats, apiGetQueueEntries, apiLeaveQueueForUser, apiSetupVenue, apiSetupStands, apiCreateLeaderboard } from '../lib/api'
import type { SportingEvent } from '../lib/types'

interface EventStats {
  waitingUsers: number
  admittedUsers: number
  completedUsers: number
  totalUsers: number
  averageWaitMinutes: number
}

const ADMIN_EMAIL = import.meta.env.VITE_ADMIN_EMAIL || 'admin@gsep.com'
const ADMIN_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD || 'admin123!'
const USE_REAL_API = import.meta.env.VITE_USE_REAL_API === 'true'

const SPORTS = ['Football', 'Tennis', 'Golf', 'Basketball', 'F1', 'Motorsport', 'Cricket', 'Rugby', 'Boxing', 'Athletics', 'Concert', 'Festival', 'Conference', 'Esports']

interface EventForm {
  title: string
  venue: string
  date: string
  time: string
  sport: string
  imageUrl: string
  totalSeats: number
  price: number
  vipPrice: number
  premiumPrice: number
  standardPrice: number
  economyPrice: number
}

const BLANK_FORM: EventForm = {
  title: '',
  venue: '',
  date: '',
  time: '',
  sport: 'Football',
  imageUrl: '',
  totalSeats: 50000,
  price: 0,
  vipPrice: 850,
  premiumPrice: 450,
  standardPrice: 250,
  economyPrice: 120,
}

function generateSeats(_sectionId: string, rows: number, seatsPerRow: number): string[] {
  const seats: string[] = []
  for (let r = 0; r < rows; r++) {
    const rowLetter = String.fromCharCode(65 + r)
    for (let s = 1; s <= seatsPerRow; s++) {
      seats.push(`${rowLetter}-${s}`)
    }
  }
  return seats
}

function generateEventId(title: string): string {
  const slug = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 40)
  return `${slug}-${Date.now().toString(36)}`
}

export default function AdminPortal() {
  const { loading } = useAuth()

  const [adminAuthed, setAdminAuthed] = useState(() =>
    sessionStorage.getItem('gsep_admin') === 'true'
  )
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginError, setLoginError] = useState('')

  const [events, setEvents] = useState<SportingEvent[]>([])
  const [eventsLoading, setEventsLoading] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState<EventForm>(BLANK_FORM)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [saved, setSaved] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<SportingEvent | null>(null)
  const [stats, setStats] = useState<EventStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)
  const [emptyingQueue, setEmptyingQueue] = useState(false)
  const [emptyQueueConfirm, setEmptyQueueConfirm] = useState(false)
  const statsTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [editingEvent, setEditingEvent] = useState<SportingEvent | null>(null)
  const [editForm, setEditForm] = useState<EventForm>(BLANK_FORM)
  const [editSaving, setEditSaving] = useState(false)
  const [editError, setEditError] = useState('')
  const [deletingEvent, setDeletingEvent] = useState<SportingEvent | null>(null)
  const [deleteConfirming, setDeleteConfirming] = useState(false)

  useEffect(() => {
    if (!adminAuthed) return
    setEventsLoading(true)
    apiGetEvents()
      .then(setEvents)
      .catch(() => setEvents([]))
      .finally(() => setEventsLoading(false))
  }, [adminAuthed])

  // Live stats polling for selected event
  useEffect(() => {
    if (!selectedEvent || !USE_REAL_API) return
    setStats(null)
    setStatsLoading(true)

    function loadStats() {
      apiGetEventStats(selectedEvent!.id)
        .then(s => { setStats(s); setStatsLoading(false) })
        .catch(() => setStatsLoading(false))
    }

    loadStats()
    statsTimerRef.current = setInterval(loadStats, 8000)
    return () => { if (statsTimerRef.current) clearInterval(statsTimerRef.current) }
  }, [selectedEvent])

  if (loading) return <div className="min-h-screen bg-[#050505]" />

  // ── Admin login ────────────────────────────────────────────
  if (!adminAuthed) {
    function handleAdminLogin(e: React.FormEvent) {
      e.preventDefault()
      if (loginEmail === ADMIN_EMAIL && loginPassword === ADMIN_PASSWORD) {
        sessionStorage.setItem('gsep_admin', 'true')
        setAdminAuthed(true)
      } else {
        setLoginError('Invalid admin credentials')
      }
    }

    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-500/10 mb-4">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.955 11.955 0 01.75 12c0 2.99 1.094 5.72 2.898 7.823A11.96 11.96 0 0012 22.25a11.96 11.96 0 008.352-2.427A11.956 11.956 0 0023.25 12c0-2.99-1.094-5.72-2.898-7.823A11.959 11.959 0 0012 2.25c-.437 0-.869.025-1.294.071" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-white">Admin Portal</h1>
            <p className="text-xs text-white/30 mt-1">Global Event Platform</p>
          </div>

          <form onSubmit={handleAdminLogin} className="space-y-4">
            {loginError && (
              <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {loginError}
              </div>
            )}
            <div>
              <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Email</label>
              <input
                type="email"
                value={loginEmail}
                onChange={e => setLoginEmail(e.target.value)}
                placeholder="admin@gsep.com"
                className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Password</label>
              <input
                type="password"
                value={loginPassword}
                onChange={e => setLoginPassword(e.target.value)}
                placeholder="••••••••"
                className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
              />
            </div>
            <button
              type="submit"
              className="w-full py-3 bg-linear-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold text-sm hover:scale-[1.02] transition-transform"
            >
              Sign In as Admin
            </button>
          </form>
          <p className="text-center text-xs text-white/20 mt-6">
            Credentials set via VITE_ADMIN_EMAIL / VITE_ADMIN_PASSWORD
          </p>
        </div>
      </div>
    )
  }

  // ── Helpers ────────────────────────────────────────────────
  async function handleSave() {
    if (!form.title || !form.venue || !form.date) return
    setSaving(true)
    setSaveError('')

    const startTime = form.time
      ? `${form.date}T${form.time}:00`
      : `${form.date}T00:00:00`

    const eventId = generateEventId(form.title)

    try {
      if (USE_REAL_API) {
        await apiCreateEvent({
          eventId,
          matchName: form.title,
          stadium: form.venue,
          capacity: form.totalSeats,
          startTime,
          status: 'OPEN',
          imageUrl: form.imageUrl,
          sport: form.sport,
          vipPrice: form.vipPrice,
          premiumPrice: form.premiumPrice,
          standardPrice: form.standardPrice,
          economyPrice: form.economyPrice,
        })
        // Seed seat inventory for each section in the seat-purchase module
        await apiSetupVenue(eventId, [
          { sectionId: 'VIP', tier: 'PREMIUM', price: form.vipPrice, seats: generateSeats('VIP', 3, 8) },
          { sectionId: 'PREMIUM', tier: 'PREMIUM', price: form.premiumPrice, seats: generateSeats('PREMIUM', 5, 12) },
          { sectionId: 'STANDARD', tier: 'STANDARD', price: form.standardPrice, seats: generateSeats('STANDARD', 8, 16) },
          { sectionId: 'ECONOMY', tier: 'GENERAL', price: form.economyPrice, seats: generateSeats('ECONOMY', 10, 20) },
        ]).catch(() => {}) // non-fatal if seat-purchase module not deployed
        
        // Seed concession stands for the event
        await apiSetupStands(eventId).catch(() => {})
        
        // Create leaderboard for the event
        await apiCreateLeaderboard(`lb-event-${eventId}`, `${form.title} Fan Leaderboard`).catch(() => {})
        
        const updated = await apiGetEvents()
        setEvents(updated)
      } else {
        const newEvent: SportingEvent = {
          id: eventId,
          title: form.title,
          venue: form.venue,
          date: form.date,
          time: form.time,
          sport: form.sport,
          imageUrl: form.imageUrl,
          totalSeats: form.totalSeats,
          availableSeats: form.totalSeats,
          price: form.economyPrice || form.price,
          status: 'OPEN',
          vipPrice: form.vipPrice,
          premiumPrice: form.premiumPrice,
          standardPrice: form.standardPrice,
          economyPrice: form.economyPrice,
        }
        setEvents(prev => [...prev, newEvent])
      }
      setCreating(false)
      setForm(BLANK_FORM)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : 'Failed to create event')
    } finally {
      setSaving(false)
    }
  }

  async function handleEmptyQueue() {
    if (!selectedEvent) return
    setEmptyingQueue(true)
    setEmptyQueueConfirm(false)
    try {
      const entries = await apiGetQueueEntries(selectedEvent.id, 'WAITING')
      await Promise.all(entries.map(e => apiLeaveQueueForUser(e.userId, selectedEvent.id)))
      // Refresh stats after clearing
      const updated = await apiGetEventStats(selectedEvent.id)
      setStats(updated)
    } catch {
      // partial clear is fine — stats will update on next poll
    } finally {
      setEmptyingQueue(false)
    }
  }

  function handleEditOpen(event: SportingEvent) {
    setEditingEvent(event)
    setEditError('')
    setEditForm({
      title: event.title,
      venue: event.venue,
      date: event.date,
      time: event.time ?? '',
      sport: event.sport ?? 'Football',
      imageUrl: event.imageUrl ?? '',
      totalSeats: event.totalSeats ?? 50000,
      price: event.price ?? 0,
      vipPrice: event.vipPrice ?? 850,
      premiumPrice: event.premiumPrice ?? 450,
      standardPrice: event.standardPrice ?? 250,
      economyPrice: event.economyPrice ?? 120,
    })
  }

  async function handleEditSave() {
    if (!editingEvent || !editForm.title || !editForm.venue || !editForm.date) return
    setEditSaving(true)
    setEditError('')
    const startTime = editForm.time
      ? `${editForm.date}T${editForm.time}:00`
      : `${editForm.date}T00:00:00`
    try {
      if (USE_REAL_API) {
        await apiUpdateEvent(editingEvent.id, {
          matchName: editForm.title,
          stadium: editForm.venue,
          capacity: editForm.totalSeats,
          startTime,
          imageUrl: editForm.imageUrl,
          sport: editForm.sport,
          vipPrice: editForm.vipPrice,
          premiumPrice: editForm.premiumPrice,
          standardPrice: editForm.standardPrice,
          economyPrice: editForm.economyPrice,
        })
        const updated = await apiGetEvents()
        setEvents(updated)
      } else {
        setEvents(prev => prev.map(e => e.id === editingEvent.id
          ? { ...e, title: editForm.title, venue: editForm.venue, date: editForm.date, time: editForm.time, totalSeats: editForm.totalSeats, price: editForm.price, imageUrl: editForm.imageUrl }
          : e
        ))
      }
      setEditingEvent(null)
    } catch (err: unknown) {
      setEditError(err instanceof Error ? err.message : 'Failed to update event')
    } finally {
      setEditSaving(false)
    }
  }

  async function handleDelete() {
    if (!deletingEvent) return
    setDeleteConfirming(true)
    try {
      if (USE_REAL_API) {
        await apiDeleteEvent(deletingEvent.id)
        const updated = await apiGetEvents()
        setEvents(updated)
      } else {
        setEvents(prev => prev.filter(e => e.id !== deletingEvent.id))
      }
      setDeletingEvent(null)
    } catch {
      // ignore — list will refresh
    } finally {
      setDeleteConfirming(false)
    }
  }

  function handleLogout() {
    sessionStorage.removeItem('gsep_admin')
    setAdminAuthed(false)
  }

  // ── UI ─────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#0a0a0a]/90 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
              <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-bold text-white">GSEP Admin</p>
              <p className="text-[10px] text-white/30">Event Management Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {saved && <span className="text-xs text-green-400 animate-pulse">✓ Event created</span>}
            <span className="text-[10px] px-2 py-1 rounded-full border border-white/10 text-white/30">
              {USE_REAL_API ? '⚡ Live API' : '💾 Local'}
            </span>
            <button
              onClick={handleLogout}
              className="text-xs text-white/40 hover:text-white border border-white/10 rounded-lg px-3 py-1.5 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Events</h1>
            <p className="text-sm text-white/30 mt-1">
              {eventsLoading ? 'Loading...' : `${events.length} events in DynamoDB`}
            </p>
          </div>
          <button
            onClick={() => { setCreating(true); setForm(BLANK_FORM); setSaveError('') }}
            className="flex items-center gap-2 px-4 py-2.5 bg-linear-to-r from-blue-500 to-blue-600 rounded-lg text-sm font-semibold hover:scale-[1.02] transition-transform"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Event
          </button>
        </div>

        {/* Events table */}
        <div className="rounded-2xl border border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5 bg-white/2">
                  <th className="px-4 py-3 text-left text-[10px] font-medium uppercase tracking-wide text-white/30">Event</th>
                  <th className="px-4 py-3 text-left text-[10px] font-medium uppercase tracking-wide text-white/30">Venue</th>
                  <th className="px-4 py-3 text-left text-[10px] font-medium uppercase tracking-wide text-white/30">Date</th>
                  <th className="px-4 py-3 text-right text-[10px] font-medium uppercase tracking-wide text-white/30">Capacity</th>
                  <th className="px-4 py-3 text-right text-[10px] font-medium uppercase tracking-wide text-white/30">Status</th>
                  <th className="px-4 py-3 text-right text-[10px] font-medium uppercase tracking-wide text-white/30">Actions</th>
                </tr>
              </thead>
              <tbody>
                {eventsLoading ? (
                  [...Array(3)].map((_, i) => (
                    <tr key={i} className="border-b border-white/3">
                      <td colSpan={6} className="px-4 py-4">
                        <div className="h-5 rounded bg-white/5 animate-pulse" />
                      </td>
                    </tr>
                  ))
                ) : events.map((event, i) => (
                  <tr
                    key={event.id}
                    className={`border-b border-white/3 hover:bg-white/2 transition-colors ${i === events.length - 1 ? 'border-b-0' : ''}`}
                  >
                    <td className="px-4 py-4">
                      <span className="font-medium text-white/80 max-w-60 truncate block">{event.title}</span>
                      <span className="text-[10px] text-white/20">{event.id}</span>
                    </td>
                    <td className="px-4 py-4 text-white/40 max-w-40 truncate">{event.venue}</td>
                    <td className="px-4 py-4 text-white/40 whitespace-nowrap">{event.date} {event.time && `· ${event.time}`}</td>
                    <td className="px-4 py-4 text-right text-white/40">{event.totalSeats?.toLocaleString()}</td>
                    <td className="px-4 py-4 text-right">
                      <span className="px-2 py-0.5 rounded-full bg-green-500/10 border border-green-500/20 text-[10px] font-medium text-green-400 uppercase">
                        {event.status ?? 'OPEN'}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setSelectedEvent(event)}
                          className="px-3 py-1.5 rounded-lg border border-white/10 text-xs text-white/50 hover:text-white hover:border-blue-500/40 transition-colors"
                        >
                          View
                        </button>
                        <button
                          onClick={() => handleEditOpen(event)}
                          className="px-3 py-1.5 rounded-lg border border-white/10 text-xs text-white/50 hover:text-white hover:border-yellow-500/40 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => setDeletingEvent(event)}
                          className="px-3 py-1.5 rounded-lg border border-white/10 text-xs text-white/50 hover:text-red-400 hover:border-red-500/40 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {!eventsLoading && events.length === 0 && (
              <div className="py-16 text-center">
                <p className="text-white/20">No events yet.</p>
                <button onClick={() => setCreating(true)} className="mt-3 text-xs text-blue-400 hover:text-blue-300">
                  Add your first event →
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Event detail / stats modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-2xl bg-[#0d0d0d] border border-white/10 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-white">{selectedEvent.title}</h2>
                <p className="text-xs text-white/30 mt-0.5">{selectedEvent.venue} · {selectedEvent.date}</p>
              </div>
              <button onClick={() => { setSelectedEvent(null); setStats(null) }} className="text-white/40 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6">
              {/* Live stats grid */}
              <p className="text-[10px] uppercase tracking-wide text-white/30 mb-4 flex items-center gap-2">
                Live Stats
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                <span className="text-white/20">refreshes every 8s</span>
              </p>

              {statsLoading && !stats ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-20 rounded-xl bg-white/3 animate-pulse" />
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="rounded-xl border border-white/5 bg-white/2 p-4">
                    <p className="text-[10px] text-white/30 uppercase tracking-wide">In Queue</p>
                    <p className="text-2xl font-bold text-yellow-400 mt-1">{stats?.waitingUsers?.toLocaleString() ?? '—'}</p>
                    <p className="text-[10px] text-white/20 mt-1">waiting for admission</p>
                  </div>
                  <div className="rounded-xl border border-white/5 bg-white/2 p-4">
                    <p className="text-[10px] text-white/30 uppercase tracking-wide">Booking Now</p>
                    <p className="text-2xl font-bold text-blue-400 mt-1">{stats?.admittedUsers?.toLocaleString() ?? '—'}</p>
                    <p className="text-[10px] text-white/20 mt-1">of 10,000 capacity</p>
                  </div>
                  <div className="rounded-xl border border-white/5 bg-white/2 p-4">
                    <p className="text-[10px] text-white/30 uppercase tracking-wide">Tickets Sold</p>
                    <p className="text-2xl font-bold text-green-400 mt-1">{stats?.completedUsers?.toLocaleString() ?? '—'}</p>
                    <p className="text-[10px] text-white/20 mt-1">completed purchases</p>
                  </div>
                  <div className="rounded-xl border border-white/5 bg-white/2 p-4">
                    <p className="text-[10px] text-white/30 uppercase tracking-wide">Seats Left</p>
                    <p className="text-2xl font-bold text-white/70 mt-1">
                      {selectedEvent.totalSeats && stats
                        ? Math.max(0, selectedEvent.totalSeats - (stats.completedUsers ?? 0)).toLocaleString()
                        : '—'
                      }
                    </p>
                    <p className="text-[10px] text-white/20 mt-1">of {selectedEvent.totalSeats?.toLocaleString()}</p>
                  </div>
                </div>
              )}

              {/* Capacity bar */}
              {stats && (
                <div className="mt-5">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] text-white/30 uppercase tracking-wide">Booking Room Usage</span>
                    <span className="text-[10px] text-white/40">{stats.admittedUsers} / 10,000</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-linear-to-r from-blue-500 to-blue-400 transition-all duration-700"
                      style={{ width: `${Math.min(100, (stats.admittedUsers / 10000) * 100)}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between mt-1.5">
                    <span className="text-[10px] text-white/30 uppercase tracking-wide">Seats Sold</span>
                    <span className="text-[10px] text-white/40">{stats.completedUsers} / {selectedEvent.totalSeats?.toLocaleString()}</span>
                  </div>
                  <div className="h-2 rounded-full bg-white/5 overflow-hidden mt-1">
                    <div
                      className="h-full rounded-full bg-linear-to-r from-green-500 to-green-400 transition-all duration-700"
                      style={{ width: `${selectedEvent.totalSeats ? Math.min(100, (stats.completedUsers / selectedEvent.totalSeats) * 100) : 0}%` }}
                    />
                  </div>
                </div>
              )}

              <div className="mt-5 pt-4 border-t border-white/5 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-[10px] text-white/30 uppercase tracking-wide">Total Registered</p>
                  <p className="text-white/70 mt-1">{stats?.totalUsers?.toLocaleString() ?? '—'}</p>
                </div>
                <div>
                  <p className="text-[10px] text-white/30 uppercase tracking-wide">Avg Wait</p>
                  <p className="text-white/70 mt-1">{stats?.averageWaitMinutes != null ? `~${stats.averageWaitMinutes} min` : '—'}</p>
                </div>
              </div>

              {/* Empty queue action */}
              <div className="mt-5 pt-4 border-t border-white/5">
                {emptyQueueConfirm ? (
                  <div className="flex items-center justify-between p-3 rounded-xl bg-red-500/5 border border-red-500/20">
                    <p className="text-xs text-red-400">Remove all {stats?.waitingUsers ?? 0} users from the queue?</p>
                    <div className="flex gap-2">
                      <button
                        onClick={handleEmptyQueue}
                        disabled={emptyingQueue}
                        className="px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/30 text-xs text-red-400 hover:bg-red-500/30 transition-colors disabled:opacity-50"
                      >
                        {emptyingQueue ? 'Clearing...' : 'Yes, Empty'}
                      </button>
                      <button
                        onClick={() => setEmptyQueueConfirm(false)}
                        className="px-3 py-1.5 rounded-lg border border-white/10 text-xs text-white/40 hover:text-white transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setEmptyQueueConfirm(true)}
                    disabled={(stats?.waitingUsers ?? 0) === 0}
                    className="w-full py-2 rounded-xl border border-red-500/20 text-xs text-red-400/60 hover:text-red-400 hover:border-red-500/40 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    Empty Queue ({stats?.waitingUsers ?? 0} waiting)
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {deletingEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-sm bg-[#0d0d0d] border border-white/10 rounded-2xl p-6">
            <h2 className="font-semibold text-white mb-2">Delete Event?</h2>
            <p className="text-sm text-white/50 mb-1">
              <span className="text-white/80">{deletingEvent.title}</span>
            </p>
            <p className="text-sm text-white/40 mb-6">
              This will permanently remove the event and its stats from DynamoDB. Queue entries are not removed.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeletingEvent(null)}
                className="flex-1 px-4 py-2 rounded-lg border border-white/10 text-sm text-white/50 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteConfirming}
                className="flex-1 px-4 py-2 rounded-lg bg-red-600/80 text-sm font-semibold text-white hover:bg-red-600 transition-colors disabled:opacity-50"
              >
                {deleteConfirming ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit event modal */}
      {editingEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-2xl bg-[#0d0d0d] border border-white/10 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
              <h2 className="font-semibold text-white">Edit Event</h2>
              <button onClick={() => setEditingEvent(null)} className="text-white/40 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              {editError && (
                <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {editError}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Event Title *</label>
                  <input
                    value={editForm.title}
                    onChange={e => setEditForm(f => ({ ...f, title: e.target.value }))}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Venue / Stadium *</label>
                  <input
                    value={editForm.venue}
                    onChange={e => setEditForm(f => ({ ...f, venue: e.target.value }))}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Date *</label>
                  <input
                    type="date"
                    value={editForm.date}
                    onChange={e => setEditForm(f => ({ ...f, date: e.target.value }))}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Time</label>
                  <input
                    type="time"
                    value={editForm.time}
                    onChange={e => setEditForm(f => ({ ...f, time: e.target.value }))}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Capacity (seats)</label>
                  <input
                    type="number"
                    min={1}
                    value={editForm.totalSeats}
                    onChange={e => setEditForm(f => ({ ...f, totalSeats: Number(e.target.value) }))}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div className="md:col-span-2">
                  <p className="text-xs font-medium text-white/50 uppercase tracking-wide mb-3">Section Pricing ($)</p>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { key: 'vipPrice', label: '🟣 VIP Box' },
                      { key: 'premiumPrice', label: '🔵 Premium Lower' },
                      { key: 'standardPrice', label: '🟢 Standard Mid' },
                      { key: 'economyPrice', label: '🟡 Economy Upper' },
                    ].map(({ key, label }) => (
                      <div key={key}>
                        <label className="text-[10px] text-white/30">{label}</label>
                        <input
                          type="number"
                          min={0}
                          value={editForm[key as keyof EventForm] as number}
                          onChange={e => setEditForm(f => ({ ...f, [key]: Number(e.target.value) }))}
                          className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Image URL (optional)</label>
                  <input
                    value={editForm.imageUrl}
                    onChange={e => setEditForm(f => ({ ...f, imageUrl: e.target.value }))}
                    placeholder="https://..."
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                  {editForm.imageUrl && (
                    <img src={editForm.imageUrl} alt="preview" className="mt-2 h-24 w-full object-cover rounded-lg opacity-60" />
                  )}
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-white/5 flex items-center justify-end gap-3">
              <button
                onClick={() => setEditingEvent(null)}
                className="px-4 py-2 rounded-lg border border-white/10 text-sm text-white/50 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleEditSave}
                disabled={!editForm.title || !editForm.venue || !editForm.date || editSaving}
                className="px-5 py-2 rounded-lg bg-linear-to-r from-yellow-500 to-yellow-600 text-sm font-semibold text-white hover:scale-[1.02] transition-transform disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {editSaving ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create event modal */}
      {creating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-2xl bg-[#0d0d0d] border border-white/10 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
              <h2 className="font-semibold text-white">Create Event</h2>
              <button onClick={() => setCreating(false)} className="text-white/40 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              {saveError && (
                <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {saveError}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Event Title *</label>
                  <input
                    value={form.title}
                    onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                    placeholder="UEFA Champions League Final"
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Venue / Stadium *</label>
                  <input
                    value={form.venue}
                    onChange={e => setForm(f => ({ ...f, venue: e.target.value }))}
                    placeholder="Wembley Stadium, London"
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Date *</label>
                  <input
                    type="date"
                    value={form.date}
                    onChange={e => setForm(f => ({ ...f, date: e.target.value }))}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Time</label>
                  <input
                    type="time"
                    value={form.time}
                    onChange={e => setForm(f => ({ ...f, time: e.target.value }))}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Sport</label>
                  <select
                    value={form.sport}
                    onChange={e => setForm(f => ({ ...f, sport: e.target.value }))}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-[#0d0d0d] px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                  >
                    {SPORTS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Capacity (seats)</label>
                  <input
                    type="number"
                    min={1}
                    value={form.totalSeats}
                    onChange={e => setForm(f => ({ ...f, totalSeats: Number(e.target.value) }))}
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                </div>

                <div className="md:col-span-2">
                  <p className="text-xs font-medium text-white/50 uppercase tracking-wide mb-3">Section Pricing ($)</p>
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { key: 'vipPrice', label: '🟣 VIP Box' },
                      { key: 'premiumPrice', label: '🔵 Premium Lower' },
                      { key: 'standardPrice', label: '🟢 Standard Mid' },
                      { key: 'economyPrice', label: '🟡 Economy Upper' },
                    ].map(({ key, label }) => (
                      <div key={key}>
                        <label className="text-[10px] text-white/30">{label}</label>
                        <input
                          type="number"
                          min={0}
                          value={form[key as keyof EventForm] as number}
                          onChange={e => setForm(f => ({ ...f, [key]: Number(e.target.value) }))}
                          className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Image URL (optional)</label>
                  <input
                    value={form.imageUrl}
                    onChange={e => setForm(f => ({ ...f, imageUrl: e.target.value }))}
                    placeholder="https://images.unsplash.com/photo-...?w=800&q=80"
                    className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
                  />
                  {form.imageUrl && (
                    <img src={form.imageUrl} alt="preview" className="mt-2 h-24 w-full object-cover rounded-lg opacity-60" />
                  )}
                </div>
              </div>
            </div>

            <div className="px-6 py-4 border-t border-white/5 flex items-center justify-end gap-3">
              <button
                onClick={() => setCreating(false)}
                className="px-4 py-2 rounded-lg border border-white/10 text-sm text-white/50 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!form.title || !form.venue || !form.date || saving}
                className="px-5 py-2 rounded-lg bg-linear-to-r from-blue-500 to-blue-600 text-sm font-semibold text-white hover:scale-[1.02] transition-transform disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {saving ? 'Creating...' : 'Create Event'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
