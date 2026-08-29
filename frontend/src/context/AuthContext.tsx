import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import type { User } from '../lib/types'
import { fetchUserAttributes, getCurrentUser } from 'aws-amplify/auth'
import { Hub } from 'aws-amplify/utils'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = async () => {
    try {
      const currentUser = await getCurrentUser()
      const attributes = await fetchUserAttributes()
      
      setUser({
        id: currentUser.userId,
        name: attributes.name || '',
        email: attributes.email || '',
        username: attributes.preferred_username || currentUser.username || '',
        phone_number: attributes.phone_number || '',
        address: attributes.address || '',
      })
    } catch (error) {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refreshUser()

    const unsubscribe = Hub.listen('auth', ({ payload }) => {
      switch (payload.event) {
        case 'signedIn':
          refreshUser()
          break
        case 'signedOut':
          setUser(null)
          break
        case 'tokenRefresh':
          refreshUser()
          break
      }
    })

    return unsubscribe
  }, [])

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, loading, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
