import { Link } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'

function RevealOnScroll({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { el.classList.add('revealed'); observer.unobserve(el) } },
      { threshold: 0.15 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])
  return <div ref={ref} className={`reveal-on-scroll ${className}`}>{children}</div>
}

function StatCounter({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center px-8 py-6 backdrop-blur-xl bg-white/2 border border-white/5 rounded-3xl hover:bg-white/4  transition-all hover:-translate-y-1">
      <p className="text-4xl md:text-5xl font-black bg-linear-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">{value}</p>
      <p className="text-xs text-white/50 mt-3 uppercase tracking-widest font-semibold">{label}</p>
    </div>
  )
}

export default function Landing() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="min-h-screen bg-[#030305] text-white overflow-hidden font-sans">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.15),transparent_60%)] blur-[100px] animate-pulse-slow" />
        <div className="absolute top-[20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[radial-gradient(circle,rgba(139,92,246,0.1),transparent_60%)] blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[20%] w-[60%] h-[60%] rounded-full bg-[radial-gradient(circle,rgba(56,189,248,0.08),transparent_60%)] blur-[150px]" />
        <div className="absolute inset-0 opacity-[0.02] bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />
      </div>

      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 px-6 py-4 transition-all duration-300 ${scrolled ? 'bg-[#030305]/80 backdrop-blur-2xl border-b border-white/5 py-4' : 'bg-transparent py-6'}`}>
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-10">
            <Link to="/" className="text-xl font-black tracking-tighter bg-linear-to-r from-white to-white/60 bg-clip-text text-transparent">
              GSEP
            </Link>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm font-medium text-white/60 hover:text-white transition-colors">Platform</a>
              <a href="#tech" className="text-sm font-medium text-white/60 hover:text-white transition-colors">Technology</a>
              <a href="#faq" className="text-sm font-medium text-white/60 hover:text-white transition-colors">FAQ</a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm font-medium text-white/70 hover:text-white transition-colors px-4 py-2 hidden sm:block">
              Log in
            </Link>
            <Link
              to="/signup"
              className="text-sm font-bold text-white bg-linear-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 px-6 py-2.5 rounded-full shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(59,130,246,0.5)] transition-all hover:scale-105"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 min-h-screen flex items-center justify-center pt-24 pb-12">
        <div className="text-center max-w-5xl mx-auto px-6">
          <RevealOnScroll>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/3 border border-white/10 mb-8 backdrop-blur-md">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-xs font-semibold text-white/70 uppercase tracking-wider">Next Gen Ticketing</span>
            </div>
          </RevealOnScroll>
          <RevealOnScroll>
            <h1 className="text-6xl md:text-8xl lg:text-[7rem] font-black leading-[1.05] tracking-tight mb-8">
              The Future of<br />
              <span className="text-transparent bg-clip-text bg-linear-to-r from-blue-400 via-indigo-400 to-purple-400">
                Live Events
              </span>
            </h1>
          </RevealOnScroll>
          <RevealOnScroll>
            <p className="text-white/50 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed font-light mb-12">
              Fair queuing. Instant seat holds. Zero double-sells. Experience the world's most advanced ticketing platform, powered by event-driven architecture.
            </p>
          </RevealOnScroll>
          <RevealOnScroll>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-5">
              <Link
                to="/signup"
                className="w-full sm:w-auto px-10 py-4 bg-white text-black rounded-full font-bold text-lg hover:bg-white/90 hover:scale-105 transition-all shadow-[0_0_30px_rgba(255,255,255,0.2)]"
              >
                Create Account
              </Link>
              <a
                href="#features"
                className="w-full sm:w-auto px-10 py-4 rounded-full border border-white/20 text-white font-semibold text-lg hover:bg-white/5 hover:border-white/40 transition-all backdrop-blur-sm"
              >
                Explore Platform
              </a>
            </div>
          </RevealOnScroll>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="relative z-10 py-16">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <StatCounter value="10M+" label="Concurrent Fans" />
            <StatCounter value="<50ms" label="Seat Hold Latency" />
            <StatCounter value="0" label="Double-Sold Tickets" />
          </div>
        </div>
      </section>

      {/* Features Showcase */}
      <section id="features" className="relative z-10 py-32">
        <div className="max-w-7xl mx-auto px-6">
          <RevealOnScroll>
            <div className="text-center mb-20">
              <h2 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">Built for Scale.</h2>
              <p className="text-xl text-white/40 font-light max-w-2xl mx-auto">
                Discover how we eliminate the chaos of high-demand ticketing with our proprietary queuing and locking mechanisms.
              </p>
            </div>
          </RevealOnScroll>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              { title: 'Smart Virtual Queuing', desc: 'Fair, position-based admission for millions of attendees. Real-time status updates and automatic promotion.', icon: '⏳', color: 'from-blue-500/20 to-cyan-500/5' },
              { title: 'Atomic Purchasing', desc: 'Secure, atomic transactions guarantee zero double-booked seats. Finalize your booking in milliseconds.', icon: '🎫', color: 'from-indigo-500/20 to-purple-500/5' },
              { title: 'Dynamic Concessions', desc: 'Pre-book VIP upgrades, merchandise, or food and beverage packages directly from your seat.', icon: '🍔', color: 'from-orange-500/20 to-red-500/5' },
              { title: 'Live Leaderboards', desc: 'Interactive dashboards, live polls, and real-time leaderboards. Connect with other attendees during the event.', icon: '🏆', color: 'from-green-500/20 to-emerald-500/5' },
              { title: 'Anti-Bot Protection', desc: 'Advanced rate limiting and behavior analysis ensures real fans get tickets, not automated scalper bots.', icon: '🛡️', color: 'from-slate-500/20 to-gray-500/5' },
              { title: 'Instant Delivery', desc: 'Secure digital tickets delivered instantly to your mobile device with dynamic QR codes.', icon: '📱', color: 'from-pink-500/20 to-rose-500/5' },
            ].map((feature) => (
              <RevealOnScroll key={feature.title}>
                <div className="group h-full p-8 rounded-3xl backdrop-blur-xl `bg-white/2` border border-white/5 hover:bg-white/4 hover:border-white/10 transition-all duration-300">
                  <div className={`w-14 h-14 rounded-2xl bg-linear-to-br ${feature.color} flex items-center justify-center text-2xl mb-6 shadow-inner`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                  <p className="text-white/40 leading-relaxed font-light">{feature.desc}</p>
                </div>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Stack */}
      <section id="tech" className="relative z-10 py-32 bg-black/40 border-y border-white/5 backdrop-blur-3xl">
        <div className="max-w-7xl mx-auto px-6">
          <RevealOnScroll>
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <div>
                <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">Serverless<br/>Architecture.</h2>
                <p className="text-lg text-white/40 font-light leading-relaxed mb-8">
                  Our platform is powered entirely by AWS Serverless technologies, enabling us to scale instantly from zero to millions of users without provisioning a single server.
                </p>
                <div className="space-y-4">
                  {[
                    { label: 'Compute', tech: 'AWS Lambda (sub-100ms cold starts)' },
                    { label: 'Database', tech: 'DynamoDB (Single-Table Design)' },
                    { label: 'Event Bus', tech: 'EventBridge (Decoupled bounded contexts)' },
                    { label: 'Buffering', tech: 'SQS (Surge protection)' },
                  ].map(item => (
                    <div key={item.label} className="flex items-center gap-4 p-4 rounded-2xl bg-white/2 border border-white/5">
                      <div className="text-xs font-bold uppercase tracking-widest text-blue-400 w-24 shrink-0">{item.label}</div>
                      <div className="text-sm font-medium text-white/70">{item.tech}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="relative">
                <div className="absolute inset-0 bg-linear-to-r from-blue-500/20 to-purple-500/20 blur-[100px]" />
                <div className="relative p-8 rounded-3xl backdrop-blur-xl bg-white/2 border border-white/10 shadow-2xl">
                  {/* Mock Code Block */}
                  <div className="flex gap-2 mb-4">
                    <div className="w-3 h-3 rounded-full bg-red-500/80" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                    <div className="w-3 h-3 rounded-full bg-green-500/80" />
                  </div>
                  <pre className="text-xs md:text-sm text-white/60 font-mono overflow-x-auto">
                    <code className="language-typescript">
{`// Atomic Seat Hold Transaction
await dynamoDB.transactWrite({
  TransactItems: [
    {
      Update: {
        TableName: 'SeatInventory',
        Key: { PK: eventId, SK: seatId },
        UpdateExpression: 'SET #status = :held',
        ConditionExpression: '#status = :available'
      }
    },
    {
      Put: {
        TableName: 'UserOrders',
        Item: orderDetails
      }
    }
  ]
});`}
                    </code>
                  </pre>
                </div>
              </div>
            </div>
          </RevealOnScroll>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="relative z-10 py-32">
        <div className="max-w-3xl mx-auto px-6">
          <RevealOnScroll>
            <div className="text-center mb-16">
              <h2 className="text-4xl md:text-5xl font-bold tracking-tight">FAQ</h2>
            </div>
          </RevealOnScroll>

          <div className="space-y-4">
            {[
              { q: 'How does the fair queuing system work?', a: 'Fans are assigned positions based on arrival time (FIFO). When capacity opens, fans are promoted in batches with admission tokens that are single-use.' },
              { q: 'Can a seat be double-sold?', a: 'No. We use DynamoDB conditional writes that atomically check seat availability before confirming. If two requests hit simultaneously, only one succeeds.' },
              { q: 'What happens if my session expires?', a: 'Purchase sessions are time-limited. If yours expires, any held seats are released back to inventory and you rejoin the queue.' },
            ].map((item, i) => (
              <RevealOnScroll key={i}>
                <details className="group rounded-2xl border border-white/10 `bg-white/2`] backdrop-blur-md overflow-hidden">
                  <summary className="flex items-center justify-between p-6 cursor-pointer text-lg font-semibold text-white/90 hover:text-white hover:bg-white/2 transition-colors">
                    {item.q}
                    <span className="text-white/40 group-open:rotate-45 transition-transform text-2xl font-light">+</span>
                  </summary>
                  <div className="px-6 pb-6 text-white/50 leading-relaxed font-light border-t border-white/5 pt-4 bg-white/1">{item.a}</div>
                </details>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 py-32 border-t border-white/5">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-150 h-100 bg-[radial-gradient(ellipse,rgba(59,130,246,0.15),transparent_70%)] blur-[100px]" />
        <div className="relative max-w-4xl mx-auto px-6 text-center">
          <RevealOnScroll>
            <h2 className="text-5xl md:text-7xl font-black mb-8 tracking-tight">Ready to join?</h2>
            <p className="text-xl text-white/40 font-light mb-12 max-w-2xl mx-auto">
              Create your account today and experience the future of live event ticketing. No queues, no crashes, just pure excitement.
            </p>
            <Link
              to="/signup"
              className="inline-block px-12 py-5 bg-white text-black rounded-full font-bold text-lg hover:bg-white/90 hover:scale-105 transition-all shadow-[0_0_40px_rgba(255,255,255,0.2)]"
            >
              Get Started Now
            </Link>
          </RevealOnScroll>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 bg-[#020202] py-12">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2 text-white/50">
            <span className="text-lg font-bold text-white">GSEP</span>
            <span className="text-sm">© 2026 Global Event Platform. All rights reserved.</span>
          </div>
          <div className="flex gap-6 text-sm text-white/40">
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-white transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
