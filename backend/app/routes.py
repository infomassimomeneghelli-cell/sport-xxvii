from __future__ import annotations

from datetime import datetime, date as date_cls
import csv
import io

from flask import Blueprint, request, abort, Response
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy import func, and_

from .app import db
from .models import User, Slot, Booking, Role
from .security import verify_password
from .utils import current_user, require_admin

api_bp = Blueprint("api", __name__)

def parse_date(s: str) -> date_cls:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        abort(400, description="Invalid date (use YYYY-MM-DD)")

@api_bp.post("/auth/login")
def login():
    data = request.get_json(force=True, silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    if not username or not password:
        abort(400, description="Missing credentials")

    user = User.query.filter(func.lower(User.email) == username, User.active.is_(True)).first()
    if not user or not verify_password(password, user.password_hash):
        abort(401, description="Invalid credentials")

    token = create_access_token(identity=str(user.id))
    return {
        "access_token": token,
        "user": {
            "id": user.id,
            "nome": user.nome,
            "cognome": user.cognome,
            "gruppo": user.gruppo,
            "role": user.role,
            "email": user.email,
        }
    }

@api_bp.get("/me")
@jwt_required()
def me():
    u = current_user()
    return {
        "id": u.id,
        "nome": u.nome,
        "cognome": u.cognome,
        "gruppo": u.gruppo,
        "role": u.role,
        "email": u.email,
    }

@api_bp.get("/slots")
@jwt_required()
def list_slots():
    u = current_user()
    date_s = request.args.get("date", "")
    if not date_s:
        abort(400, description="date is required")
    d = parse_date(date_s)
    facility = request.args.get("facility", "").strip().upper()
    # Python weekday: Monday=0..Sunday=6 => convert to 1..7
    dow = d.weekday() + 1

    q = Slot.query.filter(Slot.attivo.is_(True), Slot.giorno_settimana == dow)
    if facility:
        q = q.filter(Slot.impianto == facility)

    slots = q.order_by(Slot.impianto.asc(), Slot.ora_inizio.asc()).all()
    slot_ids = [s.id for s in slots]
    if not slot_ids:
        return {"date": date_s, "slots": []}

    counts = dict(
        db.session.query(Booking.slot_id, func.count(Booking.id))
        .filter(Booking.data == d, Booking.slot_id.in_(slot_ids))
        .group_by(Booking.slot_id)
        .all()
    )

    my_bookings = set(
        r[0] for r in db.session.query(Booking.slot_id)
        .filter(Booking.data == d, Booking.user_id == u.id, Booking.slot_id.in_(slot_ids))
        .all()
    )

    out = []
    for s in slots:
        booked = int(counts.get(s.id, 0))
        cap = s.capienza
        remaining = None if cap is None else max(cap - booked, 0)
        out.append({
            "id": s.id,
            "impianto": s.impianto,
            "titolo": s.titolo,
            "giorno_settimana": s.giorno_settimana,
            "ora_inizio": s.ora_inizio,
            "ora_fine": s.ora_fine,
            "capienza": cap,  # null => illimitata
            "attivo": s.attivo,
            "prenotati": booked,
            "rimasti": remaining,
            "prenotato_da_me": s.id in my_bookings,
            "pieno": False if cap is None else booked >= cap,
        })
    return {"date": date_s, "slots": out}

@api_bp.post("/bookings")
@jwt_required()
def create_booking():
    u = current_user()
    data = request.get_json(force=True, silent=True) or {}
    slot_id = data.get("slot_id")
    date_s = data.get("date")
    if not slot_id or not date_s:
        abort(400, description="slot_id and date required")
    d = parse_date(date_s)
    slot = db.session.get(Slot, int(slot_id))
    if not slot or not slot.attivo:
        abort(404, description="Slot not found or inactive")

    # Validate day-of-week match
    if (d.weekday() + 1) != slot.giorno_settimana:
        abort(400, description="Slot not available on selected date")

    # Prevent double booking by unique constraint + early check
    existing = Booking.query.filter_by(user_id=u.id, slot_id=slot.id, data=d).first()
    if existing:
        abort(409, description="Already booked")

    # Capacity check
    if slot.capienza is not None:
        booked = db.session.query(func.count(Booking.id)).filter_by(slot_id=slot.id, data=d).scalar() or 0
        if booked >= slot.capienza:
            abort(409, description="Slot full")

    b = Booking(user_id=u.id, slot_id=slot.id, data=d)
    db.session.add(b)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        abort(409, description="Could not book (maybe already booked)")

    return {"ok": True, "booking_id": b.id}

@api_bp.delete("/bookings/<int:booking_id>")
@jwt_required()
def delete_booking(booking_id: int):
    u = current_user()
    b = db.session.get(Booking, booking_id)
    if not b:
        abort(404, description="Booking not found")
    if b.user_id != u.id and not u.is_admin():
        abort(403, description="Not allowed")

    db.session.delete(b)
    db.session.commit()
    return {"ok": True}

@api_bp.get("/bookings/my")
@jwt_required()
def my_bookings():
    u = current_user()
    date_s = request.args.get("date", "")
    if not date_s:
        abort(400, description="date is required")
    d = parse_date(date_s)
    rows = (
        db.session.query(Booking, Slot)
        .join(Slot, Slot.id == Booking.slot_id)
        .filter(Booking.user_id == u.id, Booking.data == d)
        .all()
    )
    out = []
    for b, s in rows:
        out.append({
            "booking_id": b.id,
            "slot_id": s.id,
            "impianto": s.impianto,
            "titolo": s.titolo,
            "ora_inizio": s.ora_inizio,
            "ora_fine": s.ora_fine,
        })
    return {"date": date_s, "bookings": out}

# ---------------- ADMIN ----------------

@api_bp.get("/admin/slots")
@jwt_required()
def admin_list_slots():
    u = current_user(); require_admin(u)
    slots = Slot.query.order_by(Slot.impianto.asc(), Slot.giorno_settimana.asc(), Slot.ora_inizio.asc()).all()
    return {"slots": [{
        "id": s.id,
        "impianto": s.impianto,
        "titolo": s.titolo,
        "giorno_settimana": s.giorno_settimana,
        "ora_inizio": s.ora_inizio,
        "ora_fine": s.ora_fine,
        "capienza": s.capienza,
        "attivo": s.attivo,
    } for s in slots]}

@api_bp.post("/admin/slots")
@jwt_required()
def admin_create_slot():
    u = current_user(); require_admin(u)
    data = request.get_json(force=True, silent=True) or {}
    required = ["impianto", "titolo", "giorno_settimana", "ora_inizio", "ora_fine"]
    for k in required:
        if not data.get(k):
            abort(400, description=f"Missing {k}")
    cap = data.get("capienza", None)
    if cap in ("", None):
        cap = None
    else:
        cap = int(cap)
        if cap <= 0:
            abort(400, description="capienza must be > 0 or null")

    s = Slot(
        impianto=str(data["impianto"]).upper(),
        titolo=str(data["titolo"]).strip(),
        giorno_settimana=int(data["giorno_settimana"]),
        ora_inizio=str(data["ora_inizio"]).strip(),
        ora_fine=str(data["ora_fine"]).strip(),
        capienza=cap,
        attivo=bool(data.get("attivo", True)),
    )
    db.session.add(s); db.session.commit()
    return {"ok": True, "id": s.id}

@api_bp.put("/admin/slots/<int:slot_id>")
@jwt_required()
def admin_update_slot(slot_id: int):
    u = current_user(); require_admin(u)
    s = db.session.get(Slot, slot_id)
    if not s:
        abort(404, description="Slot not found")
    data = request.get_json(force=True, silent=True) or {}

    for field in ["impianto","titolo","giorno_settimana","ora_inizio","ora_fine","attivo"]:
        if field in data:
            if field == "impianto":
                setattr(s, field, str(data[field]).upper())
            elif field == "titolo":
                setattr(s, field, str(data[field]).strip())
            elif field == "attivo":
                setattr(s, field, bool(data[field]))
            elif field == "giorno_settimana":
                setattr(s, field, int(data[field]))
            else:
                setattr(s, field, str(data[field]).strip())

    if "capienza" in data:
        cap = data["capienza"]
        if cap in ("", None):
            s.capienza = None
        else:
            cap = int(cap)
            if cap <= 0:
                abort(400, description="capienza must be > 0 or null")
            s.capienza = cap

    db.session.commit()
    return {"ok": True}

@api_bp.post("/admin/slots/<int:slot_id>/deactivate")
@jwt_required()
def admin_deactivate_slot(slot_id: int):
    u = current_user(); require_admin(u)
    s = db.session.get(Slot, slot_id)
    if not s:
        abort(404, description="Slot not found")
    s.attivo = False
    db.session.commit()
    return {"ok": True}

@api_bp.get("/admin/bookings")
@jwt_required()
def admin_list_bookings():
    u = current_user(); require_admin(u)
    date_s = request.args.get("date", "")
    slot_id = request.args.get("slot_id", "")
    if not date_s or not slot_id:
        abort(400, description="date and slot_id required")
    d = parse_date(date_s)
    slot = db.session.get(Slot, int(slot_id))
    if not slot:
        abort(404, description="Slot not found")

    rows = (
        db.session.query(User.nome, User.cognome, User.gruppo, Booking.timestamp_creazione)
        .join(Booking, Booking.user_id == User.id)
        .filter(Booking.slot_id == slot.id, Booking.data == d)
        .order_by(User.cognome.asc(), User.nome.asc())
        .all()
    )
    return {
        "date": date_s,
        "slot": {
            "id": slot.id,
            "impianto": slot.impianto,
            "titolo": slot.titolo,
            "ora_inizio": slot.ora_inizio,
            "ora_fine": slot.ora_fine,
        },
        "prenotati": [{
            "nome": r[0],
            "cognome": r[1],
            "gruppo": r[2],
            "timestamp_creazione": r[3].isoformat() if r[3] else None
        } for r in rows]
    }

@api_bp.get("/admin/export")
@jwt_required()
def admin_export_csv():
    u = current_user(); require_admin(u)
    date_s = request.args.get("date", "")
    slot_id = request.args.get("slot_id", "")
    if not date_s or not slot_id:
        abort(400, description="date and slot_id required")
    d = parse_date(date_s)
    slot = db.session.get(Slot, int(slot_id))
    if not slot:
        abort(404, description="Slot not found")

    rows = (
        db.session.query(User.cognome, User.nome, User.gruppo, Booking.timestamp_creazione)
        .join(Booking, Booking.user_id == User.id)
        .filter(Booking.slot_id == slot.id, Booking.data == d)
        .order_by(User.cognome.asc(), User.nome.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Data", date_s])
    writer.writerow(["Impianto", slot.impianto])
    writer.writerow(["Slot", f"{slot.titolo} {slot.ora_inizio}-{slot.ora_fine}"])
    writer.writerow([])
    writer.writerow(["Cognome", "Nome", "Gruppo", "Timestamp prenotazione"])
    for c, n, g, ts in rows:
        writer.writerow([c, n, g, ts.isoformat() if ts else ""])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    filename = f"statino_{slot.impianto}_{date_s}_{slot.id}.csv"
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
