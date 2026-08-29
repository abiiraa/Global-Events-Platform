import { Link, Outlet, useNavigate, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { signOut } from 'aws-amplify/auth'

export default function AppLayout() {
  const { user, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()

  if (loading) {
    return <div className="min-h-screen bg-[#0a0a0a]" />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (isAuthenticated && !user?.username) {
    return <Navigate to="/onboarding" replace />
  }

  async function handleLogout() {
    await signOut()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[#0a0a0a]/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/dashboard" className="text-sm font-bold tracking-tight bg-linear-to-r from-blue-400 to-blue-500 bg-clip-text text-transparent">
              GEP
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link to="/dashboard" className="text-xs uppercase tracking-wide text-white/50 hover:text-white transition-colors">
                Dashboard
              </Link>
              <Link to="/events" className="text-xs uppercase tracking-wide text-white/50 hover:text-white transition-colors">
                Events
              </Link>
              <Link to="/my-matches" className="text-xs uppercase tracking-wide text-white/50 hover:text-white transition-colors">
                My Tickets
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <Link to="/profile" className="text-xs text-white/30 hidden md:block hover:text-white transition-colors">
              {user?.name}
            </Link>
            <Link to="/profile" className="w-8 h-8 rounded-full bg-linear-to-br from-blue-500 to-blue-600 flex items-center justify-center text-xs font-bold hover:scale-105 transition-transform">
              {user?.name?.charAt(0).toUpperCase()}
            </Link>
            <button
              onClick={handleLogout}
              className="text-xs text-white/40 hover:text-white transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="pt-20 min-h-screen">
        <Outlet />
      </main>
    </div>
  )
}
