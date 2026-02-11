import React, { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { useToast } from '../toast'

const DOW = [
  { v:1, t:'Lun' }, { v:2, t:'Mar' }, { v:3, t:'Mer' }, { v:4, t:'Gio' }, { v:5, t:'Ven' }, { v:6, t:'Sab' }, { v:7, t:'Dom' },
]

function todayIso() {
  const d = new Date()
  const pad = n => String(n).padStart(2,'0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`
}

export default function AdminPage() {
  const { show, Toast } = useToast()
  const [slots, setSlots] = useState([])
  const [loading, setLoading] = useState(true)

  const [form, setForm] = useState({
    impianto: 'PALESTRA',
    titolo: '',
    giorno_settimana: 1,
    ora_inizio: '16:00',
    ora_fine: '17:00',
    capienza: 30,
    attivo: true,
  })
  const [editingId, setEditingId] = useState(null)

  const [selDate, setSelDate] = useState(todayIso())
  const [selSlotId, setSelSlotId] = useState('')
  const [bookingView, setBookingView] = useState(null)
  const [busyExport, setBusyExport] = useState(false)

  async function refreshSlots() {
    setLoading(true)
    try {
      const res = await api.adminSlots()
      setSlots(res.slots)
    } catch (err) {
      show('Errore', err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refreshSlots() }, [])

  const slotsActive = useMemo(() => slots.filter(s => s.attivo), [slots])

  async function saveSlot(e) {
    e.preventDefault()
    try {
      const payload = {
        ...form,
        capienza: form.capienza === '' ? null : form.capienza,
      }
      if (editingId) {
        await api.adminUpdateSlot(editingId, payload)
        show('Slot aggiornato', 'Modifica salvata.')
      } else {
        await api.adminCreateSlot(payload)
        show('Slot creato', 'Nuovo slot inserito.')
      }
      setEditingId(null)
      setForm({
        impianto: 'PALESTRA',
        titolo: '',
        giorno_settimana: 1,
        ora_inizio: '16:00',
        ora_fine: '17:00',
        capienza: 30,
        attivo: true,
      })
      await refreshSlots()
    } catch (err) {
      show('Errore', err.message)
    }
  }

  function startEdit(s) {
    setEditingId(s.id)
    setForm({
      impianto: s.impianto,
      titolo: s.titolo,
      giorno_settimana: s.giorno_settimana,
      ora_inizio: s.ora_inizio,
      ora_fine: s.ora_fine,
      capienza: s.capienza === null ? '' : s.capienza,
      attivo: s.attivo,
    })
  }

  async function deactivate(s) {
    if (!confirm(`Disattivare lo slot: ${s.titolo} ${s.ora_inizio}-${s.ora_fine} (${s.impianto})?`)) return
    try {
      await api.adminDeactivateSlot(s.id)
      show('Slot disattivato', 'Non sarà più visibile agli utenti.')
      await refreshSlots()
    } catch (err) {
      show('Errore', err.message)
    }
  }

  async function viewBookings() {
    if (!selSlotId) return
    try {
      const res = await api.adminBookings({ date: selDate, slot_id: selSlotId })
      setBookingView(res)
    } catch (err) {
      show('Errore', err.message)
    }
  }

  async function exportCsv() {
    if (!selSlotId) return
    setBusyExport(true)
    try {
      const { blob, filename } = await api.adminExportCsvBlob({ date: selDate, slot_id: selSlotId })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
      show('Download avviato', filename)
    } catch (err) {
      show('Export fallito', err.message)
    } finally {
      setBusyExport(false)
    }
  }

  return (
    <div className="grid">
      <div className="card">
        <h2>Pannello Admin</h2>
        <div className="muted">Gestione slot (CRUD), vista prenotazioni e scarico statini CSV.</div>
      </div>

      <div className="grid cols2">
        <div className="card">
          <h2>{editingId ? `Modifica slot #${editingId}` : 'Crea nuovo slot'}</h2>
          <form onSubmit={saveSlot} className="grid">
            <div className="row">
              <div className="field" style={{minWidth:180}}>
                <label>Impianto</label>
                <select value={form.impianto} onChange={e=>setForm(f=>({...f, impianto:e.target.value}))}>
                  <option value="PALESTRA">Palestra</option>
                  <option value="CAMPI">Campi</option>
                  <option value="PISCINA">Piscina</option>
                </select>
              </div>

              <div className="field" style={{minWidth:160}}>
                <label>Giorno settimana</label>
                <select value={form.giorno_settimana} onChange={e=>setForm(f=>({...f, giorno_settimana:Number(e.target.value)}))}>
                  {DOW.map(d => <option key={d.v} value={d.v}>{d.t}</option>)}
                </select>
              </div>
            </div>

            <div className="field">
              <label>Titolo</label>
              <input className="input" value={form.titolo} onChange={e=>setForm(f=>({...f, titolo:e.target.value}))} placeholder="es. 1° Turno / Unico turno" />
            </div>

            <div className="row">
              <div className="field" style={{minWidth:160}}>
                <label>Ora inizio</label>
                <input className="input" value={form.ora_inizio} onChange={e=>setForm(f=>({...f, ora_inizio:e.target.value}))} placeholder="HH:MM" />
              </div>
              <div className="field" style={{minWidth:160}}>
                <label>Ora fine</label>
                <input className="input" value={form.ora_fine} onChange={e=>setForm(f=>({...f, ora_fine:e.target.value}))} placeholder="HH:MM" />
              </div>
            </div>

            <div className="row">
              <div className="field" style={{minWidth:200}}>
                <label>Capienza (vuoto = illimitata)</label>
                <input className="input" value={form.capienza} onChange={e=>setForm(f=>({...f, capienza:e.target.value}))} placeholder="es. 30 oppure vuoto" />
              </div>
              <div className="field" style={{minWidth:160}}>
                <label>Attivo</label>
                <select value={form.attivo ? '1' : '0'} onChange={e=>setForm(f=>({...f, attivo: e.target.value==='1'}))}>
                  <option value="1">Sì</option>
                  <option value="0">No</option>
                </select>
              </div>
            </div>

            <div className="row">
              <button className="btn primary" type="submit">{editingId ? 'Salva modifiche' : 'Crea slot'}</button>
              {editingId && <button className="btn" type="button" onClick={() => { setEditingId(null); setForm({ impianto:'PALESTRA', titolo:'', giorno_settimana:1, ora_inizio:'16:00', ora_fine:'17:00', capienza:30, attivo:true }) }}>Annulla</button>}
            </div>
          </form>
        </div>

        <div className="card">
          <h2>Vista prenotazioni + Statino</h2>
          <div className="row">
            <div className="field">
              <label>Data</label>
              <input className="input" type="date" value={selDate} onChange={e=>setSelDate(e.target.value)} />
            </div>
            <div className="field" style={{minWidth:260}}>
              <label>Slot</label>
              <select value={selSlotId} onChange={e=>setSelSlotId(e.target.value)}>
                <option value="">Seleziona…</option>
                {slotsActive.map(s => (
                  <option key={s.id} value={s.id}>
                    #{s.id} • {s.impianto} • {s.titolo} • {s.ora_inizio}-{s.ora_fine} • DOW {s.giorno_settimana}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="row">
            <button className="btn" onClick={viewBookings} disabled={!selSlotId}>Vedi prenotati</button>
            <button className="btn primary" onClick={exportCsv} disabled={!selSlotId || busyExport}>{busyExport ? 'Esporto…' : 'Scarica statino (CSV)'}</button>
          </div>

          {bookingView && (
            <>
              <hr className="sep" />
              <div style={{fontWeight:800}}>
                {bookingView.slot.impianto} • {bookingView.slot.titolo} • {bookingView.slot.ora_inizio}-{bookingView.slot.ora_fine} • {bookingView.date}
              </div>
              <div className="muted" style={{marginTop:6}}>Prenotati: {bookingView.prenotati.length}</div>
              <div style={{maxHeight:320, overflow:'auto', marginTop:10}}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Cognome</th>
                      <th>Nome</th>
                      <th>Gruppo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bookingView.prenotati.map((p, idx) => (
                      <tr key={idx}>
                        <td>{p.cognome}</td>
                        <td>{p.nome}</td>
                        <td><span className="badge">{p.gruppo}</span></td>
                      </tr>
                    ))}
                    {bookingView.prenotati.length === 0 && (
                      <tr><td colSpan="3" className="muted">Nessuna prenotazione.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>

      <div className="card">
        <h2>Elenco slot</h2>
        <div className="muted">Clicca “Modifica” oppure “Disattiva”. (Campi illimitati = capienza vuota)</div>
        <hr className="sep" />
        {loading && <div className="muted">Caricamento…</div>}
        {!loading && (
          <div style={{overflow:'auto'}}>
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Impianto</th>
                  <th>Titolo</th>
                  <th>DOW</th>
                  <th>Orario</th>
                  <th>Capienza</th>
                  <th>Attivo</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {slots.map(s => (
                  <tr key={s.id}>
                    <td>#{s.id}</td>
                    <td><span className="badge">{s.impianto}</span></td>
                    <td>{s.titolo}</td>
                    <td>{s.giorno_settimana}</td>
                    <td>{s.ora_inizio}-{s.ora_fine}</td>
                    <td>{s.capienza === null ? <span className="badge ok">Illimitata</span> : s.capienza}</td>
                    <td>{s.attivo ? <span className="badge ok">Sì</span> : <span className="badge danger">No</span>}</td>
                    <td className="row" style={{justifyContent:'flex-end'}}>
                      <button className="btn" onClick={() => startEdit(s)}>Modifica</button>
                      <button className="btn danger" onClick={() => deactivate(s)} disabled={!s.attivo}>Disattiva</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {Toast}
    </div>
  )
}
