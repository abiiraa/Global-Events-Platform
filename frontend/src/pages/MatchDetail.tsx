import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getTickets } from '../lib/store'
import { apiGetEvents, apiGetTickets } from '../lib/api'
import { useState, useEffect } from 'react'
import type { SportingEvent, Ticket } from '../lib/types'

const USE_REAL_API = import.meta.env.VITE_USE_REAL_API === 'true'

export default function MatchDetail() {
  const { eventId } = useParams<{ eventId: string }>()
  const { user } = useAuth()
  const [event, setEvent] = useState<SportingEvent | undefined>()
  const [ticket, setTicket] = useState<Ticket | undefined>()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!eventId) return
    const eventsPromise = USE_REAL_API ? apiGetEvents() : Promise.resolve([])
    const ticketsPromise = USE_REAL_API && user ? apiGetTickets(user.id) : Promise.resolve(user ? getTickets(user.id) : [])
    Promise.all([eventsPromise, ticketsPromise])
      .then(([events, tickets]) => {
        setEvent(events.find(e => e.id === eventId))
        setTicket(tickets.find(t => t.eventId === eventId))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [eventId, user])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 rounded-full border-2 border-transparent border-t-blue-500 animate-spin" />
      </div>
    )
  }

  if (!event) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-white/30">Event not found</p>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Event header */}
      <div className="relative rounded-2xl overflow-hidden mb-8">
        {event.imageUrl ? (
          <img
            src={event.imageUrl}
            alt={event.title}
            className="w-full h-48 md:h-64 object-cover"
          />
        ) : (
          <div className="w-full h-48 md:h-64 bg-linear-to-br from-blue-500/10 to-blue-600/5 flex items-center justify-center">
            <span className="text-6xl opacity-20">🏟️</span>
          </div>
        )}
        <div className="absolute inset-0 bg-linear-to-t from-[#0a0a0a] via-[#0a0a0a]/50 to-transparent" />
        <div className="absolute bottom-6 left-6">
          <h2 className="text-2xl font-bold text-white">{event.title}</h2>
          <p className="text-sm text-white/50 mt-1">{event.venue} · {event.date} · {event.time}</p>
        </div>
      </div>

      {/* Ticket info */}
      {ticket && (
        <div className="rounded-2xl border border-white/5 bg-white/2 p-6 mb-8">
          <h3 className="text-sm font-medium uppercase tracking-wide text-white/40 mb-4">Your Ticket</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-white/30">Section</p>
              <p className="text-lg font-bold text-white/90">{ticket.section}</p>
            </div>
            <div>
              <p className="text-xs text-white/30">Row</p>
              <p className="text-lg font-bold text-white/90">{ticket.row}</p>
            </div>
            <div>
              <p className="text-xs text-white/30">Seat</p>
              <p className="text-lg font-bold text-white/90">{ticket.seat}</p>
            </div>
            <div>
              <p className="text-xs text-white/30">Tier</p>
              <p className="text-lg font-bold text-blue-400">{ticket.tier}</p>
            </div>
          </div>
        </div>
      )}

      {/* Action cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-white/5 bg-white/2 p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-lg">🏆</div>
          <h3 className="font-semibold text-white/90">Leaderboard</h3>
          <p className="text-sm text-white/30">Fan engagement rankings for this event</p>
          <Link
            to={`/leaderboard/${eventId}`}
            className="inline-block px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white transition-colors"
          >
            View Rankings
          </Link>
        </div>

        <div className="rounded-2xl border border-white/5 bg-white/2 p-6 space-y-3">
          <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center text-lg">🍔</div>
          <h3 className="font-semibold text-white/90">Order Concessions</h3>
          <p className="text-sm text-white/30">Order food & beverages to your seat</p>
          <Link
            to={`/concessions/${eventId}`}
            className="inline-block px-4 py-2 rounded-lg bg-orange-500/20 text-orange-400 hover:bg-orange-500/30 text-xs font-medium transition-colors"
          >
            Order Now
          </Link>
        </div>
      </div>
    </div>
  )
}
