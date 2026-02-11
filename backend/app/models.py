from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    cognome = db.Column(db.String(80), nullable=False)
    gruppo = db.Column(db.String(80), nullable=False, default="")
    ruolo = db.Column(db.String(10), nullable=False, default="USER")  # ADMIN/USER

    email = db.Column(db.String(160), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def to_safe_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cognome": self.cognome,
            "gruppo": self.gruppo,
            "ruolo": self.ruolo,
            "email": self.email,
        }

class Slot(db.Model):
    __tablename__ = "slots"

    id = db.Column(db.Integer, primary_key=True)
    impianto = db.Column(db.String(20), nullable=False)  # PALESTRA/CAMPI/PISCINA
    titolo = db.Column(db.String(120), nullable=False)
    giorno_settimana = db.Column(db.Integer, nullable=False)  # 1=Mon..7=Sun
    ora_inizio = db.Column(db.String(5), nullable=False)  # HH:MM
    ora_fine = db.Column(db.String(5), nullable=False)    # HH:MM

    capienza = db.Column(db.Integer, nullable=True)  # None = illimitata
    attivo = db.Column(db.Boolean, nullable=False, default=True)

    def is_unlimited(self):
        return self.capienza is None

    def to_dict(self):
        return {
            "id": self.id,
            "impianto": self.impianto,
            "titolo": self.titolo,
            "giorno_settimana": self.giorno_settimana,
            "ora_inizio": self.ora_inizio,
            "ora_fine": self.ora_fine,
            "capienza": self.capienza,
            "attivo": self.attivo,
        }

class Prenotazione(db.Model):
    __tablename__ = "prenotazioni"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("slots.id"), nullable=False)
    data = db.Column(db.Date, nullable=False)
    timestamp_creazione = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref="prenotazioni")
    slot = db.relationship("Slot", backref="prenotazioni")

    # Un utente non può prenotare due volte lo stesso slot nella stessa data
    __table_args__ = (
        db.UniqueConstraint("user_id", "slot_id", "data", name="uq_user_slot_date"),
    )

