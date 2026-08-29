import { useState, useEffect, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { fetchEvents, isRegistered, registerForEvent } from '../lib/store'
import type { SportingEvent } from '../lib/types'

const CATEGORIES = ['All', 'Football', 'F1', 'Golf', 'Concert', 'Festival', 'Conference', 'Esports']

export default function Events() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [events, setEvents] = useState<SportingEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [registering, setRegistering] = useState<string | null>(null)
  
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('All')

  useEffect(() => {
    fetchEvents().then(e => { setEvents(e); setLoading(false) })
  }, [])

  async function handleRegister(eventId: string) {
    if (!user) {
      navigate('/login')
      return
    }
    setRegistering(eventId)
    await registerForEvent(user.id, eventId)
    setRegistering(null)
    navigate(`/waiting-room/${eventId}`)
  }

  const filteredEvents = useMemo(() => {
    return events.filter(e => {
      const matchSearch = e.title.toLowerCase().includes(search.toLowerCase()) || 
                          e.venue.toLowerCase().includes(search.toLowerCase())
      const matchCategory = category === 'All' || e.sport.toLowerCase() === category.toLowerCase()
      return matchSearch && matchCategory
    })
  }, [events, search, category])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="rounded-2xl border border-white/5 bg-white/2 h-72 animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-white mb-2">Explore Events</h2>
        <p className="text-white/40">Find and secure tickets to the world's most exclusive events.</p>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4 mb-10">
        <div className="relative flex-1 max-w-md">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search events, venues..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 focus:bg-white/10 transition-colors"
          />
        </div>
        
        <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
          {CATEGORIES.map(c => (
            <button
              key={c}
              onClick={() => setCategory(c)}
              className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                category === c 
                  ? 'bg-blue-600 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]' 
                  : 'bg-white/5 text-white/60 hover:bg-white/10 hover:text-white'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredEvents.map(event => {
          const registered = user ? isRegistered(user.id, event.id) : false

          return (
            <div
              key={event.id}
              className="group relative rounded-2xl border border-white/5 bg-white/2 overflow-hidden hover:border-white/10 hover:bg-white/5 transition-all duration-300"
            >
              <div className="relative h-48 overflow-hidden">
                {event.imageUrl ? (
                  <img
                    src={event.imageUrl}
                    alt={event.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
                  />
                ) : (
                  <div className="w-full h-full bg-linear-to-br from-blue-500/10 to-blue-600/5 flex items-center justify-center">
                    <span className="text-4xl opacity-30">🎟️</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-linear-to-t from-[#0a0a0a] via-transparent to-transparent opacity-80" />
                <span className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-black/40 backdrop-blur-md border border-white/10 text-[10px] font-bold uppercase tracking-wider text-white/90">
                  {event.sport}
                </span>
              </div>

              <div className="p-5 space-y-4">
                <div>
                  <h3 className="text-lg font-semibold text-white leading-tight">{event.title}</h3>
                  <div className="flex items-center gap-2 mt-2 text-xs text-white/40">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {event.venue}
                  </div>
                  <div className="flex items-center gap-2 mt-1.5 text-xs text-white/40">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {event.date}{event.time ? ` · ${event.time}` : ''}
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-white/5">
                  <div className="flex flex-col">
                    <span className="text-xs text-white/30 uppercase tracking-wide">Starting from</span>
                    <span className="text-lg font-bold text-blue-400">${event.price}</span>
                  </div>
                  
                  {registered ? (
                    <Link
                      to={`/waiting-room/${event.id}`}
                      className="px-5 py-2 rounded-lg bg-white/10 text-white text-sm font-semibold hover:bg-white/20 transition-colors"
                    >
                      View Queue
                    </Link>
                  ) : (
                    <button
                      onClick={() => handleRegister(event.id)}
                      disabled={registering === event.id}
                      className="px-5 py-2 rounded-lg bg-linear-to-r from-blue-500 to-blue-600 text-white text-sm font-semibold hover:shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all disabled:opacity-50"
                    >
                      {registering === event.id ? 'Loading...' : 'Register'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
      
      {filteredEvents.length === 0 && (
        <div className="text-center py-20">
          <span className="text-4xl">🔍</span>
          <p className="mt-4 text-white/40">No events found matching your criteria.</p>
        </div>
      )}
    </div>
  )
}
