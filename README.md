# Sport Izar SMAM

Sito web per la prenotazione di attività sportive per un corso militare (**289 utenti**).

## Funzioni principali
- **Autenticazione** (email/username + password) e ruoli: **ADMIN** / **USER**
- **Un solo ADMIN**: *Meneghelli Massimo* (gruppo **ATLA**)
- Utente **USER**: vede disponibilità e può **prenotare / annullare**
- **Admin**: CRUD slot, disattivazione slot, vista nominativi prenotati e **export statino CSV**

## Regole applicate
- Un utente **non può prenotare due volte** lo stesso slot nella stessa data (vincolo DB).
- Se la **capienza è raggiunta**, non si può prenotare.
- Per **capienza illimitata** (Campi), il limite non si applica.
- Privacy: gli utenti vedono solo conteggi e la propria prenotazione; la lista nominativa completa è solo Admin.

## Avvio locale (Windows/Mac/Linux)

### 1) Backend (Flask)
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

python init_db.py
python run.py
```

### 2) Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

Apri: `http://localhost:5173`

## Credenziali iniziali (seed)
- Utenti creati dall’Excel: `backend/data/ELENCO UNICO CORSO.xlsx` (289 righe).
- Username generato in automatico: `nome.cognome@smam.local`
- Password iniziale (uguale per tutti, modificabile da env `DEFAULT_PASSWORD`):
  - `ChangeMe123!`

> In produzione: consigliato aggiungere cambio password obbligatorio / reset password (non incluso in questa versione “MVP”).

## Slot predefiniti (seed iniziale)
- **Palestra (Lun–Ven)**  
  - 1° Turno 16:00–17:15 capienza 30  
  - 2° Turno 17:15–18:15 capienza 30  
  - 3° Turno 20:00–21:15 capienza 30
- **Campi (Lun–Ven)**  
  - Unico turno 16:00–18:15 capienza **illimitata**
- **Piscina**
  - Martedì 17:10–18:00 capienza 21
  - Mercoledì 16:20–17:10 capienza 14
  - Mercoledì 17:10–18:00 capienza 14
  - Giovedì 17:10–18:00 capienza 21

## Pagine
- `/login` — Login
- `/` — Prenotazioni (Home)
- `/admin` — Admin (solo ruolo ADMIN)
