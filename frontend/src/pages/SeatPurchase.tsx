import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getEvents, addTicket } from '../lib/store'
import { apiGetEvents, apiCreateSession, apiGetSeatMap, apiHoldSeat, apiConfirmPurchase } from '../lib/api'
import type { SportingEvent } from '../lib/types'

const USE_REAL_API = import.meta.env.VITE_USE_REAL_API === 'true'

const SECTION_META = [
  { id: 'VIP',      name: 'VIP Box',        tier: 'VIP' as const,      color: '#a855f7', rows: 3,  seatsPerRow: 8  },
  { id: 'PREMIUM',  name: 'Premium Lower',  tier: 'Premium' as const,  color: '#3b82f6', rows: 5,  seatsPerRow: 12 },
  { id: 'STANDARD', name: 'Standard Mid',   tier: 'Standard' as const, color: '#22c55e', rows: 8,  seatsPerRow: 16 },
  { id: 'ECONOMY',  name: 'Economy Upper',  tier: 'Economy' as const,  color: '#eab308', rows: 10, seatsPerRow: 20 },
]

const SEAT_VIEW_IMAGES: Record<string, string> = {
  VIP:      'https://images.unsplash.com/photo-1577223625816-7546f13df25d?w=600&q=80',
  PREMIUM:  'https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=600&q=80',
  STANDARD: 'https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=600&q=80',
  ECONOMY:  'https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=600&q=80',
}

interface SeatStatus {
  seatLabel: string
  status: 'AVAILABLE' | 'HELD' | 'SOLD'
  tier: string
  price: number
}

export default function SeatPurchase() {
  const { eventId } = useParams<{ eventId: string }>()
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
  const navigate = useNavigate()

  const [event, setEvent] = useState<SportingEvent | undefined>(() =>
    getEvents().find(e => e.id === eventId)
  )
  const [eventLoading, setEventLoading] = useState(USE_REAL_API && !event)

  const [sessionId, setSessionId] = useState<string | null>(null)
  const [sessionError, setSessionError] = useState('')
  const [sessionLoading, setSessionLoading] = useState(false)

  const [selectedSection, setSelectedSection] = useState<string | null>(null)
  const [seatStatuses, setSeatStatuses] = useState<SeatStatus[]>([])
  const [seatLoading, setSeatLoading] = useState(false)

  const [selectedSeat, setSelectedSeat] = useState<{ label: string; tier: string; price: number; sectionId: string } | null>(null)
  const [holdId, setHoldId] = useState<string | null>(null)
  const [holding, setHolding] = useState(false)
  const [holdError, setHoldError] = useState('')

  const [purchasing, setPurchasing] = useState(false)
  const [purchased, setPurchased] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load event from API
  useEffect(() => {
    if (!USE_REAL_API || !eventId) return
    apiGetEvents()
      .then(events => setEvent(events.find(e => e.id === eventId)))
      .catch(() => {})
      .finally(() => setEventLoading(false))
  }, [eventId])

  const tokenProcessingRef = useRef<string | null>(null)

  // Create purchase session when we arrive (token in URL)
  useEffect(() => {
    if (!USE_REAL_API || !eventId) return
    const token = searchParams.get('token')
    if (!token) return

    // Guard against React Strict Mode double-calling
    if (tokenProcessingRef.current === token) return
    tokenProcessingRef.current = token

    setSessionLoading(true)
    apiCreateSession(token, eventId)
      .then(r => setSessionId(r.sessionId))
      .catch(err => setSessionError(err.message ?? 'Session creation failed'))
      .finally(() => setSessionLoading(false))
  }, [eventId, searchParams])

  // Load seat map when section changes
  useEffect(() => {
    if (!selectedSection || !eventId) return
    if (!USE_REAL_API) { setSeatStatuses([]); return }
    setSeatLoading(true)
    setSeatStatuses([])
    setSelectedSeat(null)
    setHoldId(null)
    apiGetSeatMap(eventId, selectedSection)
      .then(r => setSeatStatuses((r as { seats: SeatStatus[] }).seats))
      .catch(() => {})
      .finally(() => setSeatLoading(false))
  }, [selectedSection, eventId])

  // Redirect to my-matches after purchase
  useEffect(() => {
    if (!purchased) return
    timerRef.current = setTimeout(() => navigate('/my-matches'), 3000)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [purchased, navigate])

  async function handleSelectSeat(sectionId: string, seatLabel: string, tier: string, price: number) {
    if (!USE_REAL_API || !sessionId || !eventId) {
      setSelectedSeat({ label: seatLabel, tier, price, sectionId })
      return
    }
    setHolding(true)
    setHoldError('')
    setSelectedSeat(null)
    setHoldId(null)
    try {
      const result = await apiHoldSeat(sessionId, eventId, sectionId, seatLabel)
      setHoldId(result.holdId)
      setSelectedSeat({ label: seatLabel, tier, price, sectionId })
    } catch (err: unknown) {
      setHoldError(err instanceof Error ? err.message : 'Could not hold seat — try another')
    } finally {
      setHolding(false)
    }
  }

  async function handlePurchase() {
    if (!selectedSeat || !user || !eventId) return
    setPurchasing(true)

    if (USE_REAL_API && sessionId && holdId) {
      try {
        const result = await apiConfirmPurchase(sessionId, holdId)
        addTicket({
          id: result.ticketId,
          eventId,
          userId: user.id,
          section: selectedSeat.sectionId,
          row: selectedSeat.label.split('-')[0] ?? 'A',
          seat: parseInt(selectedSeat.label.split('-')[1] ?? '1'),
          tier: selectedSeat.tier,
          price: selectedSeat.price,
          purchasedAt: new Date().toISOString(),
        })
        setPurchased(true)
      } catch (err: unknown) {
        setHoldError(err instanceof Error ? err.message : 'Purchase failed')
      } finally {
        setPurchasing(false)
      }
    } else {
      // localStorage fallback
      setTimeout(() => {
        addTicket({
          id: `tkt_${Date.now().toString(36)}`,
          eventId,
          userId: user.id,
          section: selectedSeat.sectionId,
          row: selectedSeat.label.split('-')[0] ?? 'A',
          seat: parseInt(selectedSeat.label.split('-')[1] ?? '1'),
          tier: selectedSeat.tier,
          price: selectedSeat.price,
          purchasedAt: new Date().toISOString(),
        })
        setPurchased(true)
        setPurchasing(false)
      }, 1200)
    }
  }

  // ── Thank you screen ─────────────────────────────────────────────────────────
  if (purchased && selectedSeat && event) {
    return (
      <div className="flex items-center justify-center min-h-[70vh] px-6">
        <div className="max-w-sm w-full text-center">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-green-500/10 flex items-center justify-center">
            <svg className="w-10 h-10 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Thank You!</h2>
          <p className="text-white/50 mb-6">Your ticket has been confirmed.</p>
          <div className="rounded-2xl border border-white/5 bg-white/2 p-5 text-left space-y-3 mb-6">
            <h3 className="font-semibold text-white/90">{event.title}</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><p className="text-white/30 text-xs">Section</p><p className="text-white/80">{selectedSeat.sectionId}</p></div>
              <div><p className="text-white/30 text-xs">Seat</p><p className="text-white/80">{selectedSeat.label}</p></div>
              <div><p className="text-white/30 text-xs">Tier</p><p className="text-white/80">{selectedSeat.tier}</p></div>
              <div><p className="text-white/30 text-xs">Price</p><p className="text-blue-400 font-bold">${selectedSeat.price}</p></div>
            </div>
          </div>
          <p className="text-xs text-white/20">Redirecting to My Matches…</p>
        </div>
      </div>
    )
  }

  // ── Loading / not found guards ───────────────────────────────────────────────
  if (eventLoading || sessionLoading) {
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

  if (sessionError) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] flex-col gap-4">
        <p className="text-red-400">{sessionError}</p>
        <button onClick={() => navigate('/dashboard')} className="text-xs text-white/40 hover:text-white">
          ← Back to Dashboard
        </button>
      </div>
    )
  }

  // Section prices — from DynamoDB event or defaults
  const sectionPrices: Record<string, number> = {
    VIP:      event.vipPrice      ?? 850,
    PREMIUM:  event.premiumPrice  ?? 450,
    STANDARD: event.standardPrice ?? 250,
    ECONOMY:  event.economyPrice  ?? 120,
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold tracking-tight text-white">{event.title}</h2>
        <p className="text-sm text-white/30 mt-1">{event.venue} · {event.date}</p>
        {!sessionId && USE_REAL_API && (
          <p className="text-xs text-yellow-400/70 mt-2">No session — browsing without a token. Seat holds require an admission token.</p>
        )}
      </div>

      <div className="grid gap-8 lg:grid-cols-[1fr_380px]">
        {/* Left — section + seat grid */}
        <div className="space-y-6">
          <div className="relative rounded-2xl border border-white/5 bg-white/2 p-6 overflow-hidden">
            <p className="text-xs text-white/30 uppercase tracking-wide mb-4">Select a section</p>
            <div className="space-y-3">
              {SECTION_META.map(section => (
                <button
                  key={section.id}
                  onClick={() => setSelectedSection(selectedSection === section.id ? null : section.id)}
                  className={`w-full py-3 px-4 rounded-xl border text-left transition-all duration-300 flex items-center justify-between ${
                    selectedSection === section.id
                      ? 'border-white/20 bg-white/5 scale-[1.01]'
                      : 'border-white/5 bg-white/1 hover:border-white/10'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: section.color }} />
                    <span className="text-sm font-medium text-white/80">{section.name}</span>
                  </div>
                  <span className="text-sm font-bold" style={{ color: section.color }}>
                    ${sectionPrices[section.id]}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {selectedSection && (
            <div className="rounded-2xl border border-white/5 bg-white/2 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-white/60">
                  {SECTION_META.find(s => s.id === selectedSection)?.name} — Choose your seat
                </h3>
                <div className="flex items-center gap-3 text-[10px] text-white/30">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-white/20" /> Available</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-blue-500" /> Selected</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-red-500/30" /> Sold</span>
                </div>
              </div>

              {seatLoading ? (
                <div className="h-32 flex items-center justify-center">
                  <div className="w-5 h-5 rounded-full border-2 border-transparent border-t-blue-500 animate-spin" />
                </div>
              ) : (() => {
                const meta = SECTION_META.find(s => s.id === selectedSection)!
                const price = sectionPrices[selectedSection]

                // Build seat grid — from API if available, else generate all-available
                const seatMap: Record<string, 'AVAILABLE' | 'HELD' | 'SOLD'> = {}
                if (USE_REAL_API && seatStatuses.length > 0) {
                  seatStatuses.forEach(s => { seatMap[s.seatLabel] = s.status })
                }

                return (
                  <div className="space-y-1.5 overflow-x-auto">
                    {Array.from({ length: meta.rows }, (_, row) => {
                      const rowLetter = String.fromCharCode(65 + row)
                      return (
                        <div key={row} className="flex items-center gap-1">
                          <span className="w-6 text-[10px] text-white/20 shrink-0">{rowLetter}</span>
                          <div className="flex gap-1">
                            {Array.from({ length: meta.seatsPerRow }, (_, seat) => {
                              const label = `${rowLetter}-${seat + 1}`
                              const apiStatus = seatMap[label]
                              const isSold = apiStatus === 'SOLD' || apiStatus === 'HELD'
                              const isSelected = selectedSeat?.label === label && selectedSeat?.sectionId === selectedSection
                              return (
                                <button
                                  key={seat}
                                  disabled={isSold || holding}
                                  onClick={() => !isSold && handleSelectSeat(selectedSection, label, meta.tier, price)}
                                  className={`w-6 h-6 rounded-sm text-[8px] font-medium transition-all ${
                                    isSelected
                                      ? 'bg-blue-500 text-white scale-110'
                                      : isSold
                                      ? 'bg-red-500/20 text-white/10 cursor-not-allowed'
                                      : 'bg-white/10 text-white/30 hover:bg-white/20 hover:text-white/60'
                                  }`}
                                >
                                  {seat + 1}
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )
              })()}

              {holdError && (
                <p className="mt-3 text-xs text-red-400">{holdError}</p>
              )}
            </div>
          )}
        </div>

        {/* Right — seat view + purchase panel */}
        <div className="space-y-6">
          {selectedSeat && selectedSection && (
            <div className="rounded-2xl border border-white/5 overflow-hidden">
              <div className="relative h-48">
                <img
                  src={SEAT_VIEW_IMAGES[selectedSection] ?? SEAT_VIEW_IMAGES.STANDARD}
                  alt="View from seat"
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-linear-to-t from-[#0a0a0a] via-transparent to-[#0a0a0a]/30" />
                <div className="absolute bottom-3 left-3">
                  <span className="px-2 py-1 rounded bg-black/60 backdrop-blur text-[10px] text-white/80">
                    View from {SECTION_META.find(s => s.id === selectedSection)?.name} · {selectedSeat.label}
                  </span>
                </div>
              </div>
            </div>
          )}

          <div className="rounded-2xl border border-white/5 bg-white/2 p-6 space-y-5">
            <h3 className="font-semibold text-white/90">Your Selection</h3>

            {selectedSeat ? (
              <>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-white/40">Section</span>
                    <span className="text-white/80 font-medium">{SECTION_META.find(s => s.id === selectedSeat.sectionId)?.name}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-white/40">Seat</span>
                    <span className="text-white/80 font-medium">{selectedSeat.label}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-white/40">Tier</span>
                    <span className="text-white/80 font-medium">{selectedSeat.tier}</span>
                  </div>
                  <div className="border-t border-white/5 pt-3 flex justify-between">
                    <span className="text-white/60 font-medium">Total</span>
                    <span className="text-xl font-bold text-blue-400">${selectedSeat.price}</span>
                  </div>
                </div>

                <button
                  onClick={handlePurchase}
                  disabled={purchasing || (USE_REAL_API && !holdId)}
                  className="w-full py-3 rounded-lg bg-linear-to-r from-blue-500 to-blue-600 text-white text-sm font-semibold hover:scale-[1.02] transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {purchasing ? 'Processing…' : USE_REAL_API && !holdId ? 'Holding seat…' : 'Confirm Purchase'}
                </button>
              </>
            ) : (
              <p className="text-sm text-white/20">Select a section and seat to continue</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
