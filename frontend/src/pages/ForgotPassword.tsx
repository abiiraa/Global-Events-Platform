import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { resetPassword, confirmResetPassword } from 'aws-amplify/auth'

export default function ForgotPassword() {
  const navigate = useNavigate()
  
  const [step, setStep] = useState<'request' | 'reset'>('request')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleRequest(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    
    if (!email) {
      setError('Please enter your email')
      return
    }

    setIsSubmitting(true)
    try {
      await resetPassword({ username: email })
      setStep('reset')
    } catch (err: any) {
      setError(err.message || 'Failed to request reset code')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleReset(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    
    if (!code || !newPassword) {
      setError('Please fill in all fields')
      return
    }

    setIsSubmitting(true)
    try {
      await confirmResetPassword({
        username: email,
        confirmationCode: code,
        newPassword
      })
      
      setSuccess('Password reset successful. Redirecting to login...')
      setTimeout(() => {
        navigate('/login')
      }, 2000)
    } catch (err: any) {
      setError(err.message || 'Failed to reset password')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center px-6 relative overflow-hidden">
      <div className="absolute top-[-30%] right-[-20%] w-[60%] h-[60%] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.08),transparent_60%)] blur-3xl" />
      
      <div className="relative z-10 w-full max-w-sm">
        <div className="text-center mb-8">
          <Link to="/" className="text-lg font-bold bg-linear-to-r from-blue-400 to-blue-500 bg-clip-text text-transparent">
            GEP
          </Link>
          <h1 className="text-2xl font-bold text-white mt-6">Reset Password</h1>
          <p className="text-sm text-white/40 mt-1">
            {step === 'request' ? 'Enter your email to receive a code' : `Enter the code sent to ${email}`}
          </p>
        </div>

        {step === 'request' ? (
          <form onSubmit={handleRequest} className="space-y-4">
            {error && (
              <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="text-xs font-medium text-white/50 uppercase tracking-wide">Email</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
              />
            </div>
            
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 bg-linear-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold text-sm hover:scale-[1.02] transition-transform disabled:opacity-50 disabled:hover:scale-100"
            >
              {isSubmitting ? 'Sending...' : 'Send Reset Code'}
            </button>
            
            <p className="text-center text-sm text-white/30 mt-6">
              Remember your password?{' '}
              <Link to="/login" className="text-blue-400 hover:text-blue-300 font-medium">Sign in</Link>
            </p>
          </form>
        ) : (
          <form onSubmit={handleReset} className="space-y-4">
            {error && (
              <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}
            
            {success && (
              <div className="px-4 py-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm">
                {success}
              </div>
            )}

            <div>
              <label htmlFor="code" className="text-xs font-medium text-white/50 uppercase tracking-wide">Reset Code</label>
              <input
                id="code"
                type="text"
                value={code}
                onChange={e => setCode(e.target.value)}
                placeholder="123456"
                className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors text-center tracking-widest text-lg"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="text-xs font-medium text-white/50 uppercase tracking-wide">New Password</label>
              <input
                id="password"
                type="password"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                placeholder="Min 8 characters"
                className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-blue-500/50 transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !!success}
              className="w-full py-3 bg-linear-to-r from-blue-500 to-blue-600 text-white rounded-lg font-semibold text-sm hover:scale-[1.02] transition-transform disabled:opacity-50 disabled:hover:scale-100"
            >
              {isSubmitting ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
