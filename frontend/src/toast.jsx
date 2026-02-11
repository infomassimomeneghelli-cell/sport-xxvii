import React, { useEffect, useState } from 'react'

export function useToast() {
  const [toast, setToast] = useState(null)

  function show(title, message) {
    setToast({ title, message })
  }

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 3500)
    return () => clearTimeout(t)
  }, [toast])

  const Toast = toast ? (
    <div className="toast">
      <strong>{toast.title}</strong>
      <div className="muted">{toast.message}</div>
    </div>
  ) : null

  return { show, Toast }
}
