from __future__ import annotations

import os
import re
import unicodedata
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

from app.app import create_app, db
from app.models import User, Slot, Role
from app.security import hash_password

DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "ChangeMe123!")

def slugify(s: str) -> str:
    s = str(s).strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

def seed_slots():
    # Clear existing slots
    Slot.query.delete()

    def add(impianto, titolo, dow, start, end, cap):
        db.session.add(Slot(
            impianto=impianto,
            titolo=titolo,
            giorno_settimana=dow,
            ora_inizio=start,
            ora_fine=end,
            capienza=cap,
            attivo=True
        ))

    # Palestra (Lun–Ven): 3 turni
    for dow in range(1, 6):
        add("PALESTRA", "1° Turno", dow, "16:00", "17:15", 30)
        add("PALESTRA", "2° Turno", dow, "17:15", "18:15", 30)
        add("PALESTRA", "3° Turno", dow, "20:00", "21:15", 30)

    # Campi (Lun–Ven): illimitata => capienza NULL
    for dow in range(1, 6):
        add("CAMPI", "Unico turno", dow, "16:00", "18:15", None)

    # Piscina:
    add("PISCINA", "Turno unico", 2, "17:10", "18:00", 21)  # Martedì
    add("PISCINA", "Turno 1", 3, "16:20", "17:10", 14)      # Mercoledì
    add("PISCINA", "Turno 2", 3, "17:10", "18:00", 14)      # Mercoledì
    add("PISCINA", "Turno unico", 4, "17:10", "18:00", 21)  # Giovedì

def seed_users_from_excel(excel_path: str):
    df = pd.read_excel(excel_path)

    # Expect the provided format: 4 useful columns with header "Unnamed: ..."
    df = df[df[df.columns[0]].notna()].copy()
    df.columns = ["idx", "gruppo", "cognome", "nome", *df.columns[4:]]
    df = df[["gruppo", "cognome", "nome"]]

    # Clear existing users
    User.query.delete()

    seen = set()
    for _, r in df.iterrows():
        gruppo = str(r["gruppo"]).strip()
        cognome = str(r["cognome"]).strip()
        nome = str(r["nome"]).strip()

        base = f"{slugify(nome)}.{slugify(cognome)}"
        username = base
        i = 2
        while username in seen:
            username = f"{base}{i}"
            i += 1
        seen.add(username)
        email = f"{username}@smam.local"

        role = Role.USER.value
        if cognome.upper() == "MENEGHELLI" and nome.upper() == "MASSIMO":
            role = Role.ADMIN.value

        db.session.add(User(
            nome=nome.title(),
            cognome=cognome.title(),
            gruppo=gruppo,
            role=role,
            email=email.lower(),
            password_hash=hash_password(DEFAULT_PASSWORD),
            active=True
        ))

def ensure_single_admin():
    admins = User.query.filter_by(role=Role.ADMIN.value).all()
    if not admins:
        raise RuntimeError("No ADMIN user found (expected Meneghelli Massimo).")
    if len(admins) > 1:
        raise RuntimeError(f"More than one ADMIN found ({len(admins)}). This is not allowed.")

if __name__ == "__main__":
    load_dotenv()
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Seed slots
        seed_slots()

        # Seed users
        excel_path = os.path.join(os.path.dirname(__file__), "data", "ELENCO UNICO CORSO.xlsx")
        if os.path.exists(excel_path):
            seed_users_from_excel(excel_path)
        else:
            # Minimal fallback: only admin
            db.session.add(User(
                nome="Massimo",
                cognome="Meneghelli",
                gruppo="ATLA",
                role=Role.ADMIN.value,
                email="meneghelli.massimo@smam.local",
                password_hash=hash_password(DEFAULT_PASSWORD),
                active=True
            ))

        db.session.commit()
        ensure_single_admin()

        print("✅ DB initialized.")
        print(f"✅ Seeded users: {User.query.count()} (DEFAULT_PASSWORD={DEFAULT_PASSWORD})")
        print(f"✅ Seeded slots: {Slot.query.count()}")
