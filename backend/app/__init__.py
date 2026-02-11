import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    database_url = os.getenv("DATABASE_URL", "sqlite:///local.db")
    jwt_secret = os.getenv("JWT_SECRET", "dev_secret_change_me")

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET"] = jwt_secret

    cors_origins = os.getenv("CORS_ORIGINS", "*")
    # CORS_ORIGINS può essere "*" oppure lista separata da virgole
    if cors_origins.strip() == "*":
        CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    else:
        origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
        CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True)

    db.init_app(app)

    from app.routes import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    return app
