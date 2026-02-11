import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from werkzeug.security import check_password_hash

from app import db
from app.models import User

def create_token(user: User) -> str:
    secret = current_app.config["JWT_SECRET"]
    payload = {
        "sub": user.id,
        "ruolo": user.ruolo,
        "exp": datetime.utcnow() + timedelta(hours=12),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_token(token: str):
    secret = current_app.config["JWT_SECRET"]
    return jwt.decode(token, secret, algorithms=["HS256"])

def get_bearer_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return auth.split(" ", 1)[1].strip()

def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = get_bearer_token()
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            payload = decode_token(token)
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        user = db.session.get(User, payload.get("sub"))
        if not user:
            return jsonify({"error": "User not found"}), 401

        request.user = user
        return fn(*args, **kwargs)
    return wrapper

def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = get_bearer_token()
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            payload = decode_token(token)
        except Exception:
            return jsonify({"error": "Invalid token"}), 401

        user = db.session.get(User, payload.get("sub"))
        if not user:
            return jsonify({"error": "User not found"}), 401
        if user.ruolo != "ADMIN":
            return jsonify({"error": "Admin only"}), 403

        request.user = user
        return fn(*args, **kwargs)
    return wrapper
