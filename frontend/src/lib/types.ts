export interface User {
  id: string
  name: string
  email: string
  username?: string
  phone_number?: string
  address?: string
  createdAt?: string
}

export interface SportingEvent {
  id: string
  title: string
  venue: string
  date: string
  time: string
  sport: string
  imageUrl: string
  totalSeats: number
  availableSeats: number
  price: number
  status?: string
  vipPrice?: number
  premiumPrice?: number
  standardPrice?: number
  economyPrice?: number
}

export interface Ticket {
  id: string
  eventId: string
  userId: string
  section: string
  row: string
  seat: number
  tier: string
  price: number
  purchasedAt: string
}

export interface SeatInfo {
  id: string
  section: string
  row: string
  number: number
  tier: 'VIP' | 'Premium' | 'Standard' | 'Economy'
  price: number
  status: 'available' | 'held' | 'sold'
}
