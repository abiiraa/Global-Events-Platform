import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiGetEvents, apiGetTopN, apiSubmitScore, apiGetParticipantProfile } from '../lib/api'
import { getEvents } from '../lib/store'
import type { SportingEvent } from '../lib/types'

const USE_REAL_API = import.meta.env.VITE_USE_REAL_API === 'true'

export default function Leaderboard() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  
  const [event, setEvent] = useState<SportingEvent | undefined>()
  const [rankings, setRankings] = useState<any[]>([])
  const [myScore, setMyScore] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [pointsToAdd, setPointsToAdd] = useState(10)

  // In a real app, the leaderboard ID might be linked to the event ID.
  const leaderboardId = `lb-event-${eventId}`

  const loadData = async () => {
    try {
      const events = USE_REAL_API ? await apiGetEvents() : getEvents()
      const currentEvent = events.find(e => e.id === eventId)
      setEvent(currentEvent)

      if (USE_REAL_API) {
        // Fetch top N
        const topN = await apiGetTopN(leaderboardId, 10).catch(() => ({ rankings: [] }))
        setRankings(topN.rankings || [])

        if (user) {
          const profile = await apiGetParticipantProfile(user.id).catch(() => null)
          if (profile) {
            const lb = profile.leaderboards.find((b: any) => b.leaderboardId === leaderboardId)
            if (lb) setMyScore(lb.score)
          }
        }
      }
    } catch (err) {
      console.error('Failed to load leaderboard data', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!eventId) return
    loadData()
  }, [eventId, user])

  const handleScore = async () => {
    if (!user || !USE_REAL_API) {
      alert("Must be logged in and using real API to submit scores.")
      return
    }
    
    setIsSubmitting(true)
    try {
      const newScore = (myScore || 0) + pointsToAdd
      await apiSubmitScore({
        leaderboardId,
        participantId: user.id,
        participantName: user.name,
        score: newScore,
      })
      await loadData() // Refresh board
    } catch (err: any) {
      alert(`Failed to submit score: ${err.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 rounded-full border-2 border-transparent border-t-purple-500 animate-spin" />
      </div>
    )
  }

  if (!event) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-6">
        <h2 className="text-xl font-bold text-white mb-2">Event Not Found</h2>
        <button onClick={() => navigate('/dashboard')} className="px-6 py-2 rounded-lg bg-white/10 text-white font-medium hover:bg-white/20 transition-colors">
          Back to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-500/20 text-purple-400 text-3xl mb-4">
          🏆
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">{event.title} Fan Leaderboard</h1>
        <p className="text-white/50 max-w-lg mx-auto">
          Engage with the event, purchase concessions, and cheer for your team to climb the ranks. Powered by a highly concurrent sharded DynamoDB backend.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <div className="rounded-2xl border border-white/10 bg-black overflow-hidden">
            <div className="grid grid-cols-[3rem_1fr_6rem] gap-4 p-4 border-b border-white/5 text-xs font-semibold tracking-wider text-white/40 uppercase bg-white/2">
              <div className="text-center">Rank</div>
              <div>Fan</div>
              <div className="text-right">Score</div>
            </div>
            
            <div className="divide-y divide-white/5">
              {rankings.length === 0 ? (
                <div className="p-12 text-center text-white/30 text-sm">
                  No scores submitted yet. Be the first!
                </div>
              ) : (
                rankings.map((r, i) => (
                  <div key={r.participantId} className={`grid grid-cols-[3rem_1fr_6rem] gap-4 p-4 items-center transition-colors hover:bg-white/5 ${r.participantId === user?.id ? 'bg-purple-500/10' : ''}`}>
                    <div className="text-center font-mono font-bold text-white/50">
                      {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}
                    </div>
                    <div className="font-medium text-white truncate">
                      {r.participantName}
                      {r.participantId === user?.id && <span className="ml-2 text-xs text-purple-400 font-bold">(You)</span>}
                    </div>
                    <div className="text-right font-mono font-bold text-purple-300">
                      {r.score.toLocaleString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div>
          <div className="sticky top-8 rounded-2xl bg-gradient-to-br from-purple-900/30 to-black border border-purple-500/20 p-6 text-center">
            <h3 className="text-lg font-semibold text-white/90 mb-2">Your Score</h3>
            <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 mb-6 font-mono">
              {myScore !== null ? myScore.toLocaleString() : '0'}
            </div>
            
            <div className="space-y-3">
              <p className="text-sm text-white/40 mb-4">Simulate fan engagement to earn points.</p>
              <div className="flex gap-2 justify-center mb-4">
                {[10, 50, 100].map(pts => (
                  <button
                    key={pts}
                    onClick={() => setPointsToAdd(pts)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${pointsToAdd === pts ? 'bg-purple-500 text-white' : 'bg-white/5 text-white/50 hover:bg-white/10'}`}
                  >
                    +{pts}
                  </button>
                ))}
              </div>
              <button
                onClick={handleScore}
                disabled={isSubmitting || !user}
                className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold transition-all shadow-[0_0_20px_rgba(147,51,234,0.3)] disabled:opacity-50 disabled:shadow-none"
              >
                {isSubmitting ? 'Simulating...' : `Simulate Engagement (+${pointsToAdd})`}
              </button>
              {!user && <p className="text-xs text-red-400 mt-2">Log in to submit scores</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
