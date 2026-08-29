import { createBrowserRouter, Navigate } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import ForgotPassword from './pages/ForgotPassword'
import Profile from './pages/Profile'
import Dashboard from './pages/Dashboard'
import Events from './pages/Events'
import WaitingRoom from './pages/WaitingRoom'
import SeatPurchase from './pages/SeatPurchase'
import MyMatches from './pages/MyMatches'
import MatchDetail from './pages/MatchDetail'
import AdminPortal from './pages/AdminPortal'
import Concessions from './pages/Concessions'
import Leaderboard from './pages/Leaderboard'
import Onboarding from './pages/Onboarding'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Landing />,
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/signup',
    element: <Signup />,
  },
  {
    path: '/forgot-password',
    element: <ForgotPassword />,
  },
  {
    path: '/onboarding',
    element: <Onboarding />,
  },
  {
    element: <AppLayout />,
    children: [
      {
        path: '/dashboard',
        element: <Dashboard />,
      },
      {
        path: '/events',
        element: <Events />,
      },
      {
        path: '/waiting-room/:eventId',
        element: <WaitingRoom />,
      },
      {
        path: '/purchase/:eventId',
        element: <SeatPurchase />,
      },
      {
        path: '/my-matches',
        element: <MyMatches />,
      },
      {
        path: '/match/:eventId',
        element: <MatchDetail />,
      },
      {
        path: '/concessions/:eventId',
        element: <Concessions />,
      },
      {
        path: '/leaderboard/:eventId',
        element: <Leaderboard />,
      },
      {
        path: '/profile',
        element: <Profile />,
      },
    ],
  },
  {
    path: '/admin',
    element: <AdminPortal />,
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
])
