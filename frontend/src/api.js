const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000/api'

export function getToken() {
  return localStorage.getItem('token')
}

export function setToken(t) {
  if (!t) localStorage.removeItem('token')
  else localStorage.setItem('token', t)
}

async function request(path, { method='GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  const t = token ?? getToken()
  if (t) headers['Authorization'] = `Bearer ${t}`
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  let payload = null
  const text = await res.text()
  try { payload = text ? JSON.parse(text) : null } catch { payload = { message: text } }
  if (!res.ok) {
    const msg = payload?.description || payload?.message || `Errore ${res.status}`
    const err = new Error(msg)
    err.status = res.status
    err.payload = payload
    throw err
  }
  return payload
}

export const api = {
  login: (username, password) => request('/auth/login', { method:'POST', body:{ username, password }, token: null }),
  me: () => request('/me'),
  slots: ({ date, facility }) => request(`/slots?date=${encodeURIComponent(date)}${facility ? `&facility=${encodeURIComponent(facility)}` : ''}`),
  myBookings: ({ date }) => request(`/bookings/my?date=${encodeURIComponent(date)}`),
  book: ({ slot_id, date }) => request('/bookings', { method:'POST', body:{ slot_id, date } }),
  cancel: (booking_id) => request(`/bookings/${booking_id}`, { method:'DELETE' }),

  adminSlots: () => request('/admin/slots'),
  adminCreateSlot: (data) => request('/admin/slots', { method:'POST', body:data }),
  adminUpdateSlot: (id, data) => request(`/admin/slots/${id}`, { method:'PUT', body:data }),
  adminDeactivateSlot: (id) => request(`/admin/slots/${id}/deactivate`, { method:'POST' }),
  adminBookings: ({ date, slot_id }) => request(`/admin/bookings?date=${encodeURIComponent(date)}&slot_id=${encodeURIComponent(slot_id)}`),
  adminExportUrl: ({ date, slot_id }) => {
    const t = getToken()
    // CSV download uses Authorization header; easiest is to open in new tab with token via query param? We avoid that.
    // Instead we fetch as blob in UI. This URL is still useful for debugging.
    return `${API_BASE}/admin/export?date=${encodeURIComponent(date)}&slot_id=${encodeURIComponent(slot_id)}`
  },
  adminExportCsvBlob: async ({ date, slot_id }) => {
    const t = getToken()
    const url = `${API_BASE}/admin/export?date=${encodeURIComponent(date)}&slot_id=${encodeURIComponent(slot_id)}`
    const res = await fetch(url, { headers: { 'Authorization': `Bearer ${t}` } })
    if (!res.ok) throw new Error(`Export fallito (${res.status})`)
    const blob = await res.blob()
    const filename = res.headers.get('Content-Disposition')?.split('filename=')?.[1]?.replaceAll('"','') || 'statino.csv'
    return { blob, filename }
  }
}
