import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { fetchTickets } from '../lib/store'
import { apiGetEvents } from '../lib/api'
import { useState, useEffect } from 'react'
import type { Ticket, SportingEvent } from '../lib/types'

const USE_REAL_API = import.meta.env.VITE_USE_REAL_API === 'true'

export default function MyMatches() {
  const { user } = useAuth()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [events, setEvents] = useState<SportingEvent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const eventsPromise = USE_REAL_API ? apiGetEvents() : Promise.resolve([])
    if (!user) {
      eventsPromise.then(setEvents).catch(() => {})
      setLoading(false)
      return
    }
    Promise.all([
      fetchTickets(user.id),
      eventsPromise,
    ]).then(([t, e]) => { setTickets(t); setEvents(e) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="space-y-3">
          {[1, 2].map(i => (
            <div key={i} className="h-20 rounded-xl border border-white/5 bg-white/2 animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-10">
        <h2 className="text-2xl font-bold tracking-tight bg-linear-to-r from-white to-white/70 bg-clip-text text-transparent">
          My Matches
        </h2>
        <p className="text-sm text-white/30 mt-1">Your purchased tickets</p>
      </div>

      {tickets.length > 0 ? (
        <div className="space-y-3">
          {tickets.map(ticket => {
            const event = events.find(e => e.id === ticket.eventId)
            return (
              <div key={ticket.id} className="flex items-center justify-between p-5 rounded-xl border border-white/5 bg-white/2">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-linear-to-br from-blue-500/20 to-blue-400/20 flex items-center justify-center text-lg">
                    🎫
                  </div>
                  <div>
                    <h4 className="font-medium text-white/90">{event?.title || ticket.eventId}</h4>
                    <p className="text-xs text-white/30">
                      Section {ticket.section} · Row {ticket.row} · Seat {ticket.seat} · {ticket.tier}
                    </p>
                  </div>
                </div>
                <Link
                  to={`/match/${ticket.eventId}`}
                  className="px-4 py-2 rounded-lg border border-white/10 text-xs font-medium text-white/60 hover:text-white hover:border-white/20 transition-all"
                >
                  View Match
                </Link>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-20">
          <p className="text-white/20 text-lg mb-4">No tickets yet</p>
          <Link to="/dashboard" className="text-blue-400 text-sm hover:text-blue-300 font-medium">
            Browse events →
          </Link>
        </div>
      )}
    </div>
  )
}
