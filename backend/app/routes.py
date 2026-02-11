from datetime import datetime
import csv
import io

from flask import Blueprint, jsonify, request, Response
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

from app import db
from app.models import User, Slot, Prenotazione
from app.auth import create_token, require_auth, require_admin

bp = Blueprint("api", __name__)

def parse_date(date_str: str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def weekday_1_to_7(d):
    # python: Monday=0..Sunday=6
    return d.weekday() + 1

@bp.post("/auth/login")
def login():
    data = request.get_json(force=True)
    identifier = (data.get("email") or data.get("username") or "").strip().lower()
    password = (data.get("password") or "").strip()

    if not identifier or not password:
        return jsonify({"error": "Missing credentials"}), 400

    user = User.query.filter(func.lower(User.email) == identifier).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_token(user)
    return jsonify({"token": token, "user": user.to_safe_dict()})

@bp.get("/me")
@require_auth
def me():
    return jsonify({"user": request.user.to_safe_dict()})

@bp.get("/slots")
@require_auth
def get_slots_for_date():
    date_str = request.args.get("date", "").strip()
    impianto = (request.args.get("impianto") or "").strip().upper()

    if not date_str:
        return jsonify({"error": "Missing date"}), 400

    d = parse_date(date_str)
    dow = weekday_1_to_7(d)

    q = Slot.query.filter_by(attivo=True, giorno_settimana=dow)
    if impianto:
        q = q.filter(Slot.impianto == impianto)

    slots = q.order_by(Slot.ora_inizio.asc()).all()

    # prenotazioni per slot in quella data
    counts = dict(
        db.session.query(Prenotazione.slot_id, func.count(Prenotazione.id))
        .filter(Prenotazione.data == d)
        .group_by(Prenotazione.slot_id)
        .all()
    )

    # prenotazioni dell'utente in quella data (per mostrare "Prenotato")
    my_booked = set(
        r[0] for r in db.session.query(Prenotazione.slot_id)
        .filter(Prenotazione.data == d, Prenotazione.user_id == request.user.id)
        .all()
    )

    result = []
    for s in slots:
        booked = int(counts.get(s.id, 0))
        if s.capienza is None:
            rimasti = None
            pieno = False
        else:
            rimasti = max(s.capienza - booked, 0)
            pieno = booked >= s.capienza

        result.append({
            **s.to_dict(),
            "prenotati": booked,
            "rimasti": rimasti,  # None = illimitati
            "pieno": pieno,
            "prenotato_da_me": (s.id in my_booked),
        })

    return jsonify({"date": date_str, "slots": result})

@bp.post("/bookings")
@require_auth
def book():
    data = request.get_json(force=True)
    slot_id = data.get("slot_id")
    date_str = (data.get("date") or "").strip()

    if not slot_id or not date_str:
        return jsonify({"error": "Missing slot_id/date"}), 400

    d = parse_date(date_str)
    slot = db.session.get(Slot, int(slot_id))
    if not slot or not slot.attivo:
        return jsonify({"error": "Slot not found/inactive"}), 404

    # slot valido per giorno settimana?
    if slot.giorno_settimana != weekday_1_to_7(d):
        return jsonify({"error": "Slot not available on this date"}), 400

    # già prenotato da me?
    existing = Prenotazione.query.filter_by(
        user_id=request.user.id,
        slot_id=slot.id,
        data=d
    ).first()
    if existing:
        return jsonify({"error": "Already booked"}), 409

    # capienza?
    if slot.capienza is not None:
        booked = db.session.query(func.count(Prenotazione.id)).filter(
            Prenotazione.slot_id == slot.id,
            Prenotazione.data == d
        ).scalar() or 0

        if booked >= slot.capienza:
            return jsonify({"error": "Full"}), 409

    b = Prenotazione(user_id=request.user.id, slot_id=slot.id, data=d)
    db.session.add(b)
    db.session.commit()
    return jsonify({"ok": True})

@bp.delete("/bookings")
@require_auth
def cancel_booking():
    data = request.get_json(force=True)
    slot_id = data.get("slot_id")
    date_str = (data.get("date") or "").strip()

    if not slot_id or not date_str:
        return jsonify({"error": "Missing slot_id/date"}), 400

    d = parse_date(date_str)
    b = Prenotazione.query.filter_by(
        user_id=request.user.id,
        slot_id=int(slot_id),
        data=d
    ).first()
    if not b:
        return jsonify({"error": "Not booked"}), 404

    db.session.delete(b)
    db.session.commit()
    return jsonify({"ok": True})

# ---------------- ADMIN ----------------

@bp.get("/admin/slots")
@require_admin
def admin_list_slots():
    slots = Slot.query.order_by(Slot.giorno_settimana.asc(), Slot.ora_inizio.asc()).all()
    return jsonify({"slots": [s.to_dict() for s in slots]})

@bp.post("/admin/slots")
@require_admin
def admin_create_slot():
    data = request.get_json(force=True)

    cap = data.get("capienza")
    capienza = None if cap in (None, "", "illimitata", "ILLIMITATA") else int(cap)

    s = Slot(
        impianto=str(data["impianto"]).upper(),
        titolo=str(data["titolo"]).strip(),
        giorno_settimana=int(data["giorno_settimana"]),
        ora_inizio=str(data["ora_inizio"]).strip(),
        ora_fine=str(data["ora_fine"]).strip(),
        capienza=capienza,
        attivo=bool(data.get("attivo", True)),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({"slot": s.to_dict()})

@bp.put("/admin/slots/<int:slot_id>")
@require_admin
def admin_update_slot(slot_id):
    s = db.session.get(Slot, slot_id)
    if not s:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True)

    if "impianto" in data: s.impianto = str(data["impianto"]).upper()
    if "titolo" in data: s.titolo = str(data["titolo"]).strip()
    if "giorno_settimana" in data: s.giorno_settimana = int(data["giorno_settimana"])
    if "ora_inizio" in data: s.ora_inizio = str(data["ora_inizio"]).strip()
    if "ora_fine" in data: s.ora_fine = str(data["ora_fine"]).strip()
    if "attivo" in data: s.attivo = bool(data["attivo"])

    if "capienza" in data:
        cap = data["capienza"]
        s.capienza = None if cap in (None, "", "illimitata", "ILLIMITATA") else int(cap)

    db.session.commit()
    return jsonify({"slot": s.to_dict()})

@bp.get("/admin/bookings")
@require_admin
def admin_bookings_for_slot_date():
    date_str = request.args.get("date", "").strip()
    slot_id = request.args.get("slot_id", "").strip()

    if not date_str or not slot_id:
        return jsonify({"error": "Missing date/slot_id"}), 400

    d = parse_date(date_str)
    slot = db.session.get(Slot, int(slot_id))
    if not slot:
        return jsonify({"error": "Slot not found"}), 404

    bookings = (
        db.session.query(Prenotazione, User)
        .join(User, User.id == Prenotazione.user_id)
        .filter(Prenotazione.slot_id == slot.id, Prenotazione.data == d)
        .order_by(User.cognome.asc(), User.nome.asc())
        .all()
    )

    people = [{
        "nome": u.nome,
        "cognome": u.cognome,
        "gruppo": u.gruppo,
        "email": u.email
    } for _, u in bookings]

    return jsonify({
        "date": date_str,
        "slot": slot.to_dict(),
        "prenotati": people
    })

@bp.get("/admin/export")
@require_admin
def admin_export_csv():
    date_str = request.args.get("date", "").strip()
    slot_id = request.args.get("slot_id", "").strip()

    if not date_str or not slot_id:
        return jsonify({"error": "Missing date/slot_id"}), 400

    d = parse_date(date_str)
    slot = db.session.get(Slot, int(slot_id))
    if not slot:
        return jsonify({"error": "Slot not found"}), 404

    rows = (
        db.session.query(User)
        .join(Prenotazione, Prenotazione.user_id == User.id)
        .filter(Prenotazione.slot_id == slot.id, Prenotazione.data == d)
        .order_by(User.cognome.asc(), User.nome.asc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Cognome", "Nome", "Gruppo", "Email/Username"])
    for u in rows:
        writer.writerow([u.cognome, u.nome, u.gruppo, u.email])

    filename = f"statino_{slot.impianto}_{date_str}_slot{slot.id}.csv".replace(":", "-")
    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
