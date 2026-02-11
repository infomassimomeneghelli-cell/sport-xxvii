import React, { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { useToast } from '../toast'

function fmtDow(d) {
  const dow = d.getDay() // 0 Sun .. 6 Sat
  const map = ['Domenica','Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato']
  return map[dow]
}

function todayIso() {
  const d = new Date()
  const pad = n => String(n).padStart(2,'0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`
}

export default function BookingPage() {
  const { show, Toast } = useToast()
  const [date, setDate] = useState(todayIso())
  const [facility, setFacility] = useState('')
  const [slots, setSlots] = useState([])
  const [myBookings, setMyBookings] = useState([])
  const [busyId, setBusyId] = useState(null)
  const [loading, setLoading] = useState(true)

  const dayLabel = useMemo(() => fmtDow(new Date(date)), [date])

  async function refresh() {
    setLoading(true)
    try {
      const res = await api.slots({ date, facility: facility || undefined })
      setSlots(res.slots)
      const mine = await api.myBookings({ date })
      setMyBookings(mine.bookings)
    } catch (err) {
      show('Errore', err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [date, facility])

  const myBookingBySlot = useMemo(() => {
    const m = new Map()
    for (const b of myBookings) m.set(b.slot_id, b)
    return m
  }, [myBookings])

  async function onBook(slot) {
    setBusyId(slot.id)
    try {
      await api.book({ slot_id: slot.id, date })
      show('Prenotazione confermata', `${slot.titolo} • ${slot.impianto} • ${slot.ora_inizio}-${slot.ora_fine}`)
      await refresh()
    } catch (err) {
      show('Impossibile prenotare', err.message)
    } finally {
      setBusyId(null)
    }
  }

  async function onCancel(slot) {
    const b = myBookingBySlot.get(slot.id)
    if (!b) return
    setBusyId(slot.id)
    try {
      await api.cancel(b.booking_id)
      show('Prenotazione annullata', `${slot.titolo} • ${slot.impianto}`)
      await refresh()
    } catch (err) {
      show('Impossibile annullare', err.message)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="grid">
      <div className="card">
        <h2>Prenotazioni</h2>
        <div className="row">
          <div className="field">
            <label>Data</label>
            <input className="input" type="date" value={date} onChange={e=>setDate(e.target.value)} />
            <div className="muted" style={{fontSize:12}}>{dayLabel}</div>
          </div>
          <div className="field">
            <label>Filtro impianto (opzionale)</label>
            <select value={facility} onChange={e=>setFacility(e.target.value)}>
              <option value="">Tutti</option>
              <option value="PALESTRA">Palestra</option>
              <option value="CAMPI">Campi</option>
              <option value="PISCINA">Piscina</option>
            </select>
          </div>
          <button className="btn" onClick={refresh} disabled={loading}>Aggiorna</button>
        </div>
      </div>

      <div className="grid">
        {loading && <div className="card">Caricamento slot…</div>}
        {!loading && slots.length === 0 && (
          <div className="card">
            <div className="muted">Nessuno slot attivo per la data selezionata.</div>
          </div>
        )}

        {!loading && slots.map(s => {
          const mine = myBookingBySlot.get(s.id)
          const unlimited = s.capienza === null
          const remainingLabel = unlimited ? 'Illimitati' : String(s.rimasti)
          const statusBadge = mine
            ? <span className="badge ok">Prenotato</span>
            : s.pieno
              ? <span className="badge danger">Pieno</span>
              : <span className="badge">Disponibile</span>

          return (
            <div className="card" key={s.id}>
              <div className="row" style={{justifyContent:'space-between'}}>
                <div>
                  <div style={{fontWeight:800,fontSize:16}}>
                    {s.titolo} • {s.ora_inizio}-{s.ora_fine}
                  </div>
                  <div className="muted">{s.impianto}</div>
                </div>
                <div className="row">
                  {statusBadge}
                </div>
              </div>

              <hr className="sep" />
              <div className="row" style={{justifyContent:'space-between'}}>
                <div className="row">
                  <span className="pill">Prenotati: <b>{s.prenotati}</b></span>
                  <span className="pill">Rimasti: <b>{remainingLabel}</b></span>
                </div>

                {!mine && (
                  <button className="btn primary" disabled={s.pieno || busyId===s.id} onClick={() => onBook(s)}>
                    {busyId===s.id ? 'Prenoto…' : 'Prenota'}
                  </button>
                )}
                {mine && (
                  <button className="btn danger" disabled={busyId===s.id} onClick={() => onCancel(s)}>
                    {busyId===s.id ? 'Annullo…' : 'Annulla'}
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {Toast}
    </div>
  )
}
