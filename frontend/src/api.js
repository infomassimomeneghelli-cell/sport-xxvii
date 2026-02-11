// frontend/src/api.js

// Base URL dell'API
export const API_BASE =
  import.meta.env.VITE_API_URL || "https://sport-xxvii-api.onrender.com";

// Helper per gestire il token
export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  localStorage.setItem("token", token);
}

export function removeToken() {
  localStorage.removeItem("token");
}

// Funzione generica per chiamate API
export async function apiFetch(endpoint, options = {}) {
  const token = getToken();

  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "API error");
  }

  return res.json();
}

// ---- AUTH ----

export async function login(email, password) {
  const data = await apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  setToken(data.token);
  return data.user;
}

// ---- USER ----

export function getMe() {
  return apiFetch("/api/me");
}

// ---- SLOTS ----

export function getSlots(date, impianto = "") {
  const params = new URLSearchParams({ date });
  if (impianto) params.append("impianto", impianto);

  return apiFetch(`/api/slots?${params.toString()}`);
}

// ---- PRENOTAZIONI ----

export function bookSlot(slot_id, date) {
  return apiFetch("/api/bookings", {
    method: "POST",
    body: JSON.stringify({ slot_id, date }),
  });
}

export function cancelSlot(slot_id, date) {
  return apiFetch("/api/bookings", {
    method: "DELETE",
    body: JSON.stringify({ slot_id, date }),
  });
}
