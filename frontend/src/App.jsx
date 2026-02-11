import React from 'react'
import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import LoginPage from './pages/LoginPage'
import BookingPage from './pages/BookingPage'
import AdminPage from './pages/AdminPage'

function Shell({ children }) {
  const { user, logout } = useAuth()
  const loc = useLocation()
  return (
    <div className="container">
      <div className="topbar">
        <div className="brand">
          <div className="title">Sport Izar SMAM</div>
          <div className="subtitle">Prenotazione attività sportive — corso militare</div>
        </div>

        {user && (
          <div className="row">
            <span className="pill">{user.cognome} {user.nome} • {user.gruppo} • {user.role}</span>
            <Link className="btn" to="/">Prenotazioni</Link>
            {user.role === 'ADMIN' && <Link className="btn" to="/admin">Admin</Link>}
            <button className="btn danger" onClick={logout}>Logout</button>
          </div>
        )}
        {!user && loc.pathname !== '/login' && <Link className="btn" to="/login">Login</Link>}
      </div>

      {children}
      <div style={{marginTop:18}} className="muted">
        © {new Date().getFullYear()} • Layout “aeronautico” scuro • Privacy: nominativi completi visibili solo ad ADMIN.
      </div>
    </div>
  )
}

function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  const loc = useLocation()
  if (loading) return <div className="card">Caricamento…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return children
}

function RequireAdmin({ children }) {
  const { user } = useAuth()
  if (user?.role !== 'ADMIN') return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <Shell>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<RequireAuth><BookingPage /></RequireAuth>} />
          <Route path="/admin" element={<RequireAuth><RequireAdmin><AdminPage /></RequireAdmin></RequireAuth>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Shell>
    </AuthProvider>
  )
}
