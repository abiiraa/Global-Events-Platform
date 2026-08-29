import { useState, useEffect } from 'react'
import { updateUserAttributes } from 'aws-amplify/auth'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const { user, refreshUser } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (user) {
      setName(user.name || '')
      setPhone(user.phone_number || '')
      setAddress(user.address || '')
    }
  }, [user])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setIsSubmitting(true)

    try {
      const attributes: Record<string, string> = { name }
      if (phone) attributes.phone_number = phone
      if (address) attributes.address = address

      await updateUserAttributes({
        userAttributes: attributes
      })
      await refreshUser()
      setSuccess('Profile updated successfully!')
      setIsEditing(false)
    } catch (err: any) {
      setError(err.message || 'Failed to update profile')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!user) return null

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-white">Your Profile</h1>
        {!isEditing && (
          <button
            onClick={() => setIsEditing(true)}
            className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm text-white hover:bg-white/10 transition-colors"
          >
            Edit Profile
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}
      
      {success && (
        <div className="mb-6 px-4 py-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm">
          {success}
        </div>
      )}

      <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Full Name</label>
              {isEditing ? (
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  className="mt-2 w-full rounded-lg border border-white/10 bg-black/20 px-4 py-2 text-sm text-white focus:border-blue-500/50 outline-none"
                />
              ) : (
                <div className="mt-2 text-white">{user.name}</div>
              )}
            </div>

            <div>
              <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Email</label>
              <div className="mt-2 text-white/50">{user.email} (Cannot be changed)</div>
            </div>

            <div>
              <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Username</label>
              <div className="mt-2 text-white/50">{user.username || 'Not set'} (Cannot be changed)</div>
            </div>

            <div>
              <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Phone Number</label>
              {isEditing ? (
                <input
                  type="tel"
                  value={phone}
                  onChange={e => setPhone(e.target.value)}
                  placeholder="+1234567890"
                  className="mt-2 w-full rounded-lg border border-white/10 bg-black/20 px-4 py-2 text-sm text-white focus:border-blue-500/50 outline-none"
                />
              ) : (
                <div className="mt-2 text-white">{user.phone_number || 'Not provided'}</div>
              )}
            </div>

            <div>
              <label className="text-xs font-medium text-white/50 uppercase tracking-wide">Address</label>
              {isEditing ? (
                <input
                  type="text"
                  value={address}
                  onChange={e => setAddress(e.target.value)}
                  placeholder="Your address"
                  className="mt-2 w-full rounded-lg border border-white/10 bg-black/20 px-4 py-2 text-sm text-white focus:border-blue-500/50 outline-none"
                />
              ) : (
                <div className="mt-2 text-white">{user.address || 'Not provided'}</div>
              )}
            </div>
          </div>

          {isEditing && (
            <div className="pt-4 flex justify-end gap-3 border-t border-white/10">
              <button
                type="button"
                onClick={() => {
                  setIsEditing(false)
                  setName(user.name || '')
                  setPhone(user.phone_number || '')
                  setAddress(user.address || '')
                  setError('')
                }}
                className="px-4 py-2 text-sm text-white/50 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
