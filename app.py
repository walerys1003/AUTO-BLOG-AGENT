"""
MasterContentAI - Flask app factory.

Sets up:
- SQLAlchemy
- Session management (7-day permanent sessions) with secure cookies
- CSRF protection (Flask-WTF)
- Rate limiting (Flask-Limiter)
- The new DB-backed authentication system (auth.py)
- All routes via routes.register_routes(app)
"""

import logging
import os
from datetime import timedelta

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.orm import DeclarativeBase

from config import Config

# ---- Logging ----
# Use INFO in production, DEBUG only when FLASK_DEBUG=1
_log_level = logging.DEBUG if os.environ.get("FLASK_DEBUG") == "1" else logging.INFO
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---- SQLAlchemy ----
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


# ---- Flask app ----
app = Flask(__name__)
app.secret_key = Config.SESSION_SECRET

# Detect production mode (any non-development env)
_is_production = os.environ.get("FLASK_ENV", "production").lower() != "development"

app.config.update(
    SQLALCHEMY_DATABASE_URI=Config.DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        "pool_recycle": 300,
        "pool_pre_ping": True,
    },
    # ---- Secure session cookies ----
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=_is_production and os.environ.get("FORCE_HTTPS", "false").lower() == "true",
    SESSION_COOKIE_NAME="mcai_session",
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    # ---- CSRF ----
    WTF_CSRF_TIME_LIMIT=None,  # CSRF tokens valid for the lifetime of the session
    WTF_CSRF_SSL_STRICT=_is_production,
)

# Initialise DB
db.init_app(app)

# ---- CSRF protection ----
csrf = CSRFProtect(app)


@app.context_processor
def inject_csrf():
    """Make csrf_token() available in every template."""
    from flask_wtf.csrf import generate_csrf
    return {"csrf_token": generate_csrf}


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Friendly error handler for CSRF validation failures."""
    logger.warning("CSRF validation failed: %s (path=%s)", e.description, request.path)
    if request.is_json or request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "error": "Sesja wygasła lub żądanie nie zawiera tokenu CSRF. Odśwież stronę i spróbuj ponownie.",
        }), 400
    try:
        return render_template("errors/csrf.html", reason=e.description), 400
    except Exception:
        return (
            "<h1>Błąd weryfikacji formularza</h1>"
            "<p>Twoja sesja mogła wygasnąć. <a href='/'>Odśwież stronę</a> i spróbuj ponownie.</p>",
            400,
        )


# ---- Rate limiting ----
# Storage: in-memory by default; switch to Redis via RATELIMIT_STORAGE_URI env in prod
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["600 per hour", "60 per minute"],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
    headers_enabled=True,
    strategy="fixed-window",
)


# ---- Authentication ----
# Import here so models are registered with SQLAlchemy first.
from auth import auth_bp, ensure_default_admin, current_user  # noqa: E402

# Apply stricter rate limits to login endpoint
limiter.limit("10 per minute; 30 per hour", methods=["POST"])(auth_bp)

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


logger.info(
    "MasterContentAI Flask app initialised (auth + routes + CSRF + rate limiter; production=%s, secure_cookies=%s)",
    _is_production,
    app.config["SESSION_COOKIE_SECURE"],
)
