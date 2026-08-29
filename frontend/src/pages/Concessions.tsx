import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiGetEvents, apiGetTickets, apiPlaceOrder, apiGetFanOrders } from '../lib/api'
import { getEvents, getTickets } from '../lib/store'
import type { SportingEvent, Ticket } from '../lib/types'

const USE_REAL_API = import.meta.env.VITE_USE_REAL_API === 'true'

// Dummy menu
const MENU_ITEMS = [
  { id: 'nachos', name: 'Loaded Nachos', price: 12, icon: '🧀' },
  { id: 'hotdog', name: 'Stadium Hot Dog', price: 8, icon: '🌭' },
  { id: 'pretzel', name: 'Soft Pretzel', price: 6, icon: '🥨' },
  { id: 'beer', name: 'Draft Beer', price: 10, icon: '🍺' },
  { id: 'soda', name: 'Fountain Soda', price: 5, icon: '🥤' },
]

export default function Concessions() {
  const { eventId } = useParams<{ eventId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()
  
  const [event, setEvent] = useState<SportingEvent | undefined>()
  const [ticket, setTicket] = useState<Ticket | undefined>()
  const [loading, setLoading] = useState(true)
  const [cart, setCart] = useState<Record<string, number>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [activeOrders, setActiveOrders] = useState<any[]>([])

  useEffect(() => {
    if (!eventId || !user) return

    const loadData = async () => {
      try {
        const events = USE_REAL_API ? await apiGetEvents() : getEvents()
        const currentEvent = events.find(e => e.id === eventId)
        setEvent(currentEvent)

        const tickets = USE_REAL_API ? await apiGetTickets(user.id) : getTickets(user.id)
        const currentTicket = tickets.find(t => t.eventId === eventId)
        setTicket(currentTicket)

        if (USE_REAL_API && currentTicket) {
          const ordersRes = await apiGetFanOrders(user.id, eventId)
          setActiveOrders(ordersRes.orders.filter(o => !['PICKED_UP', 'CANCELLED'].includes(o.status)))
        }
      } catch (err) {
        console.error('Failed to load concessions data', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [eventId, user])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-6 h-6 rounded-full border-2 border-transparent border-t-orange-500 animate-spin" />
      </div>
    )
  }

  if (!event || !ticket) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-6">
        <h2 className="text-xl font-bold text-white mb-2">Ticket Required</h2>
        <p className="text-white/50 mb-6">You need a valid ticket to this event to order concessions to your seat.</p>
        <button onClick={() => navigate(`/match/${eventId}`)} className="px-6 py-2 rounded-lg bg-white/10 text-white font-medium hover:bg-white/20 transition-colors">
          Back to Match
        </button>
      </div>
    )
  }

  const handleUpdateQuantity = (itemId: string, delta: number) => {
    setCart(prev => {
      const current = prev[itemId] || 0
      const next = Math.max(0, current + delta)
      const newCart = { ...prev, [itemId]: next }
      if (next === 0) delete newCart[itemId]
      return newCart
    })
  }

  const cartItems = Object.entries(cart).map(([itemId, quantity]) => {
    const item = MENU_ITEMS.find(m => m.id === itemId)!
    return { ...item, quantity }
  })
  
  const totalPrice = cartItems.reduce((sum, item) => sum + (item.price * item.quantity), 0)
  
  const isVip = ticket.tier === 'VIP' || ticket.tier === 'Premium'

  const handleCheckout = async () => {
    if (!user || cartItems.length === 0) return
    setIsSubmitting(true)
    try {
      if (USE_REAL_API) {
        const orderItems = cartItems.map(item => ({
          itemId: item.id,
          name: item.name,
          quantity: item.quantity,
          price: item.price
        }))
        await apiPlaceOrder({
          eventId: event.id,
          fanId: user.id,
          section: ticket.section,
          items: orderItems,
          isVip,
        })
        
        // Refresh orders
        const ordersRes = await apiGetFanOrders(user.id, event.id)
        setActiveOrders(ordersRes.orders.filter(o => !['PICKED_UP', 'CANCELLED'].includes(o.status)))
      } else {
        alert("Ordered! Use real API mode to see the live queue.")
      }
      setCart({})
    } catch (err: any) {
      alert(`Checkout failed: ${err.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Order Concessions</h1>
        <p className="text-white/50">
          Ordering for Section <strong className="text-white">{ticket.section}</strong>, Row {ticket.row}, Seat {ticket.seat}
        </p>
        {isVip && (
          <span className="inline-block mt-3 px-2.5 py-1 bg-yellow-500/20 text-yellow-500 text-xs font-bold uppercase tracking-wider rounded border border-yellow-500/30">
            VIP Priority Routing Active
          </span>
        )}
      </div>

      {activeOrders.length > 0 && (
        <div className="mb-10 space-y-4">
          <h2 className="text-lg font-semibold text-white/90">Active Orders</h2>
          {activeOrders.map(order => (
            <div key={order.orderId} className="rounded-xl border border-orange-500/30 bg-orange-500/10 p-5 flex items-center justify-between">
              <div>
                <p className="text-xs text-orange-400 font-mono mb-1">#{order.orderId.substring(0, 8).toUpperCase()}</p>
                <p className="font-medium text-white">{order.status}</p>
                <p className="text-sm text-white/50 mt-1">Total: ${order.totalPrice} · Stand: {order.standName || order.standId}</p>
              </div>
              <div className="w-12 h-12 rounded-full border-2 border-orange-500/50 flex items-center justify-center animate-pulse">
                <span className="text-orange-400 text-xl">⏳</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-8">
        <div className="md:col-span-2 space-y-4">
          <h2 className="text-lg font-semibold text-white/90">Menu</h2>
          {MENU_ITEMS.map(item => {
            const quantity = cart[item.id] || 0
            return (
              <div key={item.id} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-colors">
                <div className="flex items-center gap-4">
                  <span className="text-3xl">{item.icon}</span>
                  <div>
                    <h3 className="font-medium text-white">{item.name}</h3>
                    <p className="text-sm text-white/50">${item.price}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 bg-black/40 rounded-lg p-1 border border-white/5">
                  <button 
                    onClick={() => handleUpdateQuantity(item.id, -1)}
                    disabled={quantity === 0}
                    className="w-8 h-8 rounded flex items-center justify-center text-white/50 hover:bg-white/10 hover:text-white disabled:opacity-30 disabled:hover:bg-transparent"
                  >
                    -
                  </button>
                  <span className="w-4 text-center text-sm font-medium text-white">{quantity}</span>
                  <button 
                    onClick={() => handleUpdateQuantity(item.id, 1)}
                    className="w-8 h-8 rounded flex items-center justify-center text-white/50 hover:bg-white/10 hover:text-white"
                  >
                    +
                  </button>
                </div>
              </div>
            )
          })}
        </div>

        <div>
          <div className="sticky top-8 rounded-xl bg-[#111] border border-white/10 p-6">
            <h2 className="text-lg font-semibold text-white/90 mb-4">Your Order</h2>
            {cartItems.length === 0 ? (
              <p className="text-sm text-white/40 text-center py-8">Your cart is empty</p>
            ) : (
              <>
                <div className="space-y-3 mb-6">
                  {cartItems.map(item => (
                    <div key={item.id} className="flex justify-between text-sm">
                      <span className="text-white/70">{item.quantity}x {item.name}</span>
                      <span className="text-white font-medium">${item.price * item.quantity}</span>
                    </div>
                  ))}
                </div>
                <div className="pt-4 border-t border-white/10 flex justify-between items-center mb-6">
                  <span className="font-medium text-white/70">Total</span>
                  <span className="text-2xl font-bold text-white">${totalPrice}</span>
                </div>
                <button
                  onClick={handleCheckout}
                  disabled={isSubmitting}
                  className="w-full py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold transition-colors shadow-[0_0_20px_rgba(249,115,22,0.3)] disabled:opacity-50"
                >
                  {isSubmitting ? 'Processing...' : 'Place Order'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
