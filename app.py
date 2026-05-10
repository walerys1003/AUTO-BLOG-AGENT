"""
MasterContentAI - Flask app factory.

Sets up:
- SQLAlchemy
- Session management (7-day permanent sessions)
- The new DB-backed authentication system (auth.py)
- All routes via routes.register_routes(app)
"""

import logging
import os
from datetime import timedelta

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from config import Config

# ---- Logging ----
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# ---- SQLAlchemy ----
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


# ---- Flask app ----
app = Flask(__name__)
app.secret_key = Config.SESSION_SECRET

app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.permanent_session_lifetime = timedelta(days=7)

# Initialise DB
db.init_app(app)

# ---- Authentication ----
# Import here so models are registered with SQLAlchemy first.
from auth import auth_bp, ensure_default_admin, current_user  # noqa: E402

app.register_blueprint(auth_bp)


@app.context_processor
def inject_auth_globals():
    """Make `current_user` available in every template."""
    user = current_user()
    return {
        "current_user": user,
        "is_authenticated": user is not None,
    }


# ---- Routes ----
from routes import register_routes  # noqa: E402

register_routes(app)


# ---- Bootstrap default admin on first request ----
with app.app_context():
    try:
        db.create_all()
        ensure_default_admin()
    except Exception as exc:
        logger.error("Bootstrap error: %s", exc)


logger.info("MasterContentAI Flask app initialised (auth + routes registered)")
