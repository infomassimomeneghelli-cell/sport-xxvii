import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth'
import { useToast } from '../toast'

export default function LoginPage() {
  const { login, user } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const { show, Toast } = useToast()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) nav('/', { replace: true })

  const from = loc.state?.from || '/'

  async function onSubmit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      await login(username, password)
      nav(from, { replace: true })
    } catch (err) {
      show('Login fallito', err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid cols2">
      <div className="card">
        <h2>Login</h2>
        <div className="muted" style={{marginBottom:12}}>
          Inserisci <b>email/username</b> e password.
        </div>
        <form onSubmit={onSubmit} className="grid">
          <div className="field">
            <label>Email / Username</label>
            <input className="input" value={username} onChange={e=>setUsername(e.target.value)} placeholder="es. nome.cognome@smam.local" />
          </div>
          <div className="field">
            <label>Password</label>
            <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" />
          </div>
          <button className="btn primary" disabled={busy}>{busy ? 'Accesso…' : 'Entra'}</button>
        </form>
      </div>

      <div className="card">
        <h2>Note operative</h2>
        <ul className="muted" style={{margin:0, paddingLeft:18, lineHeight:1.6}}>
          <li>Ruoli: <b>ADMIN</b> e <b>USER</b>.</li>
          <li>Solo l’admin può creare/modificare/disattivare slot e scaricare gli statini.</li>
          <li>Gli utenti vedono solo conteggi e le proprie prenotazioni.</li>
        </ul>
        <hr className="sep" />
        <div className="muted">
          Se è una prima installazione, le credenziali iniziali sono create da <code>backend/init_db.py</code>.
        </div>
      </div>
      {Toast}
    </div>
  )
}
