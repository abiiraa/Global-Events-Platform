import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { fetchEvents, getTickets } from '../lib/store'
import { useState, useEffect } from 'react'
import type { SportingEvent, Ticket } from '../lib/types'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [events, setEvents] = useState<SportingEvent[]>([])
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    
    Promise.all([
      fetchEvents(),
      getTickets(user.id)
    ]).then(([e, t]) => {
      setEvents(e)
      setTickets(t)
      setLoading(false)
    })
  }, [user, navigate])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <div className="h-32 rounded-2xl border border-white/5 bg-white/2 animate-pulse" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="rounded-2xl border border-white/5 bg-white/2 h-48 animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  // Calculate some stats
  const upcomingTickets = tickets.length // Simplification for now
  const spent = tickets.reduce((acc, t) => acc + (t.price || 0), 0)
  const hotEvents = events.slice(0, 3) // Just taking first 3 as "hot"

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Welcome Banner */}
      <div className="mb-10 p-8 rounded-3xl border border-white/10 bg-linear-to-br from-blue-900/20 to-purple-900/10 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />
        <div className="relative z-10">
          <h1 className="text-3xl font-bold text-white mb-2">Welcome back, {user?.name.split(' ')[0]}!</h1>
          <p className="text-white/60 mb-6">Here's your Global Event Platform overview.</p>
          
          <div className="flex flex-wrap gap-4">
            <div className="px-6 py-4 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm min-w-[150px]">
              <p className="text-xs text-white/40 uppercase tracking-wider mb-1">My Tickets</p>
              <p className="text-2xl font-bold text-white">{upcomingTickets}</p>
            </div>
            <div className="px-6 py-4 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm min-w-[150px]">
              <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Total Spent</p>
              <p className="text-2xl font-bold text-white">${spent}</p>
            </div>
            <Link 
              to="/my-matches"
              className="px-6 py-4 rounded-2xl bg-blue-600/20 border border-blue-500/30 text-blue-400 hover:bg-blue-600/30 transition-colors flex items-center justify-center font-medium"
            >
              View My Matches →
            </Link>
          </div>
        </div>
      </div>

      <div className="flex items-end justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">🔥 Trending Events</h2>
          <p className="text-sm text-white/40 mt-1">Events selling fast right now</p>
        </div>
        <Link to="/events" className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors">
          View all events →
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {hotEvents.map(event => (
          <Link
            key={event.id}
            to={`/events`}
            className="group relative rounded-2xl border border-white/5 bg-white/2 overflow-hidden hover:border-white/10 transition-all duration-300 block"
          >
            <div className="relative h-40 overflow-hidden">
              {event.imageUrl ? (
                <img
                  src={event.imageUrl}
                  alt={event.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
              ) : (
                <div className="w-full h-full bg-linear-to-br from-blue-500/10 to-blue-600/5 flex items-center justify-center">
                  <span className="text-4xl opacity-30">🏟️</span>
                </div>
              )}
              <div className="absolute inset-0 bg-linear-to-t from-[#0a0a0a] via-[#0a0a0a]/40 to-transparent opacity-90" />
              <div className="absolute bottom-4 left-4 right-4">
                <h3 className="font-bold text-white leading-tight">{event.title}</h3>
                <p className="text-xs text-white/60 mt-1">{event.date}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
      
      {/* Quick Actions */}
      <div className="mt-12">
        <h2 className="text-xl font-bold tracking-tight text-white mb-6">Quick Actions</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <Link to="/events" className="p-5 rounded-2xl border border-white/5 bg-white/2 hover:bg-white/5 transition-colors flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 text-lg">🎟️</div>
            <div>
              <p className="text-sm font-semibold text-white">Browse Events</p>
              <p className="text-xs text-white/40">Find your next experience</p>
            </div>
          </Link>
          <Link to="/profile" className="p-5 rounded-2xl border border-white/5 bg-white/2 hover:bg-white/5 transition-colors flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 text-lg">👤</div>
            <div>
              <p className="text-sm font-semibold text-white">Update Profile</p>
              <p className="text-xs text-white/40">Manage your details</p>
            </div>
          </Link>
          <div className="p-5 rounded-2xl border border-white/5 bg-white/2 flex items-center gap-4 opacity-50 cursor-not-allowed">
            <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center text-green-400 text-lg">🏆</div>
            <div>
              <p className="text-sm font-semibold text-white">View Leaderboards</p>
              <p className="text-xs text-white/40">Join an event first</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
