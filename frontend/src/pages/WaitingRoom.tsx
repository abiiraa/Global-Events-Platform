import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { fetchQueueStatus } from '../lib/store'
import { apiAdmitUsers, apiGetEvents, apiGetEventStats, apiLeaveQueue } from '../lib/api'

const USE_REAL_API = import.meta.env.VITE_USE_REAL_API === 'true'
const PURCHASING_CAPACITY = 10000
const BATCH_SIZE = 100

export default function WaitingRoom() {
  const { eventId } = useParams<{ eventId: string }>()
  const { user } = useAuth()
  const navigate = useNavigate()

  const [eventTitle, setEventTitle] = useState<string>('')
  const [waitMinutes, setWaitMinutes] = useState<number | null>(null)
  const [waitingCount, setWaitingCount] = useState<number | null>(null)
  const [currentlyBooking, setCurrentlyBooking] = useState<number | null>(null)
  const [admitted, setAdmitted] = useState(false)
  const [tokenId, setTokenId] = useState<string | undefined>()
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false)
  const [leaving, setLeaving] = useState(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const admitRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Fetch event title
  useEffect(() => {
    if (!eventId || !USE_REAL_API) return
    apiGetEvents().then(events => {
      const found = events.find(e => e.id === eventId)
      if (found) setEventTitle(found.title)
    }).catch(() => {})
  }, [eventId])

  // Auto-admit in batches of 100, up to 10000 capacity
  useEffect(() => {
    if (!eventId || !USE_REAL_API) return
    function triggerAdmit() {
      apiAdmitUsers(eventId!).catch(() => {})
    }
    triggerAdmit()
    admitRef.current = setInterval(triggerAdmit, 10000)
    return () => { if (admitRef.current) clearInterval(admitRef.current) }
  }, [eventId])

  // Poll queue status every 5s + refresh stats
  useEffect(() => {
    if (!user || !eventId) return

    async function poll() {
      try {
        const [status, stats] = await Promise.all([
          fetchQueueStatus(user!.id, eventId!),
          USE_REAL_API ? apiGetEventStats(eventId!) : Promise.resolve(null),
        ])

        setWaitMinutes(status.estimatedWaitMinutes ?? 0)

        if (stats) {
          setWaitingCount(stats.waitingUsers)
          setCurrentlyBooking(stats.admittedUsers)
        }

        if (status.status === 'ADMITTED') {
          setAdmitted(true)
          setTokenId(status.tokenId)
          if (pollingRef.current) clearInterval(pollingRef.current)
          if (admitRef.current) clearInterval(admitRef.current)
        }
      } catch {
        setWaitMinutes(prev => {
          if (prev === null) return 5
          const next = prev - 1
          if (next <= 0) { setAdmitted(true); return 0 }
          return next
        })
      }
    }

    poll()
    pollingRef.current = setInterval(poll, 5000)
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [user, eventId])

  useEffect(() => {
    if (admitted) {
      const timer = setTimeout(() => navigate(`/purchase/${eventId}${tokenId ? `?token=${tokenId}` : ''}`), 1500)
      return () => clearTimeout(timer)
    }
  }, [admitted, eventId, navigate, tokenId])

  async function handleLeaveQueue() {
    if (!user || !eventId) return
    setLeaving(true)
    if (pollingRef.current) clearInterval(pollingRef.current)
    if (admitRef.current) clearInterval(admitRef.current)
    try {
      await apiLeaveQueue(user.id, eventId)
    } catch {
      // proceed regardless — user wants out
    }
    navigate('/dashboard')
  }

  const displayTitle = eventTitle || eventId
  const slotsAvailable = currentlyBooking !== null ? Math.max(0, PURCHASING_CAPACITY - currentlyBooking) : null
  const batchesAhead = waitingCount !== null ? Math.ceil(waitingCount / BATCH_SIZE) : null

  return (
    <div className="max-w-lg mx-auto px-6 py-16 text-center">

      {/* Confirmation popup */}
      {showLeaveConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="mx-4 w-full max-w-sm rounded-2xl border border-white/10 bg-[#0d0d14] p-6 shadow-2xl">
            <h3 className="mb-2 text-lg font-bold text-white">Leave the queue?</h3>
            <p className="mb-6 text-sm text-white/50">
              You'll be removed from the queue and would have to enter again to book.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowLeaveConfirm(false)}
                className="flex-1 rounded-lg border border-white/10 py-2.5 text-sm font-medium text-white/60 transition hover:border-white/20 hover:text-white/80"
              >
                Cancel
              </button>
              <button
                onClick={handleLeaveQueue}
                disabled={leaving}
                className="flex-1 rounded-lg bg-red-600/80 py-2.5 text-sm font-semibold text-white transition hover:bg-red-600 disabled:opacity-50"
              >
                {leaving ? 'Leaving…' : 'Yes, leave'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Back button */}
      {!admitted && (
        <button
          onClick={() => setShowLeaveConfirm(true)}
          className="mb-8 flex items-center gap-1.5 text-sm text-white/40 transition hover:text-white/70"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
      )}

      <div className="relative w-32 h-32 mx-auto mb-10">
        <div className="absolute inset-0 rounded-full border-2 border-white/5" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-blue-500 animate-spin" style={{ animationDuration: '2s' }} />
        <div className="absolute inset-3 rounded-full border-2 border-transparent border-b-blue-400 animate-spin" style={{ animationDuration: '3s', animationDirection: 'reverse' }} />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold text-white">
            {admitted ? '✓' : waitMinutes !== null ? `${waitMinutes}m` : '…'}
          </span>
        </div>
      </div>

      <h2 className="text-xl font-bold text-white mb-2">
        {admitted ? "You're In!" : "You're in the Queue"}
      </h2>
      <p className="text-sm text-white/40 mb-8">
        {admitted
          ? 'Redirecting to seat selection...'
          : slotsAvailable !== null && slotsAvailable > 0
            ? `${slotsAvailable.toLocaleString()} booking slots available. Admitting in batches of ${BATCH_SIZE}.`
            : "Due to high demand, you've been placed in a virtual waiting room."
        }
      </p>

      {!admitted && (
        <div className="rounded-2xl border border-white/5 bg-white/2 p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-white/30 uppercase tracking-wide">Est. Wait</p>
              <p className="text-2xl font-bold text-blue-400 mt-1">
                {waitMinutes !== null ? `~${waitMinutes} min` : '…'}
              </p>
            </div>
            <div>
              <p className="text-xs text-white/30 uppercase tracking-wide">Batches Ahead</p>
              <p className="text-2xl font-bold text-white/70 mt-1">
                {batchesAhead !== null ? batchesAhead : '…'}
              </p>
            </div>
            <div>
              <p className="text-xs text-white/30 uppercase tracking-wide">In Queue</p>
              <p className="text-lg font-semibold text-white/60 mt-1">
                {waitingCount !== null ? waitingCount.toLocaleString() : '…'}
              </p>
            </div>
            <div>
              <p className="text-xs text-white/30 uppercase tracking-wide">Currently Booking</p>
              <p className="text-lg font-semibold text-white/60 mt-1">
                {currentlyBooking !== null ? `${currentlyBooking.toLocaleString()} / ${PURCHASING_CAPACITY.toLocaleString()}` : '…'}
              </p>
            </div>
          </div>
          <div className="border-t border-white/5 pt-4">
            <p className="text-xs text-white/30 uppercase tracking-wide">Event</p>
            <p className="text-sm font-medium text-white/60 mt-1">{displayTitle}</p>
          </div>
        </div>
      )}

      <p className="text-[11px] text-white/20 mt-6">
        Do not close this page. You will be admitted automatically.
      </p>
    </div>
  )
}
