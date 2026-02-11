# Sport Izar SMAM — Backend (Flask)

## Quick start
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Initialize DB + seed (users + slots)
python init_db.py

# Run API
python run.py
```

API will run on `http://localhost:5000`.
