from __future__ import annotations

from datetime import datetime
from flask import abort
from flask_jwt_extended import get_jwt_identity
from .models import User
from .app import db

def current_user() -> User:
    ident = get_jwt_identity()
    if ident is None:
        abort(401, description="Not authenticated")
    user = db.session.get(User, int(ident))
    if not user or not user.active:
        abort(401, description="User not found or inactive")
    return user

def require_admin(user: User) -> None:
    if not user.is_admin():
        abort(403, description="Admin only")
