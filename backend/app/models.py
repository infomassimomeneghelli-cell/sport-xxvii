from __future__ import annotations

from datetime import datetime, date
from enum import Enum
from sqlalchemy import UniqueConstraint
from .app import db

class Role(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"

class Facility(str, Enum):
    PALESTRA = "PALESTRA"
    CAMPI = "CAMPI"
    PISCINA = "PISCINA"

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    cognome = db.Column(db.String(80), nullable=False)
    gruppo = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(10), nullable=False, default=Role.USER.value)
    email = db.Column(db.String(120), nullable=False, unique=True)  # email/username
    password_hash = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    bookings = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan")

    def is_admin(self) -> bool:
        return self.role == Role.ADMIN.value

class Slot(db.Model):
    __tablename__ = "slots"
    id = db.Column(db.Integer, primary_key=True)
    impianto = db.Column(db.String(20), nullable=False)  # Facility
    titolo = db.Column(db.String(120), nullable=False)
    giorno_settimana = db.Column(db.Integer, nullable=False)  # 1=Mon..7=Sun
    ora_inizio = db.Column(db.String(5), nullable=False)  # HH:MM
    ora_fine = db.Column(db.String(5), nullable=False)    # HH:MM
    capienza = db.Column(db.Integer, nullable=True)       # NULL => illimitata
    attivo = db.Column(db.Boolean, nullable=False, default=True)

    bookings = db.relationship("Booking", back_populates="slot", cascade="all, delete-orphan")

class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("slots.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    timestamp_creazione = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="bookings")
    slot = db.relationship("Slot", back_populates="bookings")

    __table_args__ = (
        UniqueConstraint("user_id", "slot_id", "data", name="uq_user_slot_date"),
    )
