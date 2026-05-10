"""
MasterContentAI - Authentication & Authorisation.

Replaces the old `admin_auth.py` (env-only single user) and removes Replit Auth.
Provides:
- Database-backed users (User model) with PBKDF2 password hashing.
- Role decorators: @login_required, @admin_required, @editor_required.
- Session helpers (login / logout / current user).
- One-time bootstrap of a default admin from ADMIN_LOGIN/ADMIN_PASSWORD env vars
  (so a fresh deployment always has a way in).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify

from app import db
from models import User, UserSession, ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER, VALID_ROLES

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

SESSION_USER_KEY = "user_id"
SESSION_TOKEN_KEY = "remember_token"
REMEMBER_DAYS = 30


# =================================================================
# Bootstrap helpers
# =================================================================

def ensure_default_admin() -> None:
    """Create a default admin user if no admin exists.

    Reads ADMIN_LOGIN and ADMIN_PASSWORD from env (legacy variables).
    Only runs when the users table is empty - never overwrites existing data.
    """
    if User.query.count() > 0:
        return

    login = os.environ.get("ADMIN_LOGIN") or "admin"
    password = os.environ.get("ADMIN_PASSWORD") or "admin"
    email = os.environ.get("ADMIN_EMAIL") or f"{login}@mastercontent.ai"

    user = User(
        email=email,
        username=login,
        full_name="System Administrator",
        role=ROLE_ADMIN,
        is_active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    logger.warning(
        "Bootstrapped default admin user '%s'. Change the password immediately!",
        login,
    )


# =================================================================
# Current user helpers
# =================================================================

def current_user() -> User | None:
    """Return the currently authenticated user (cached on flask.g)."""
    if hasattr(g, "_current_user"):
        return g._current_user

    user: User | None = None
    user_id = session.get(SESSION_USER_KEY)
    if user_id:
        user = User.query.filter_by(id=user_id, is_active=True).first()

    # Try persistent "remember me" token
    if user is None:
        token = session.get(SESSION_TOKEN_KEY) or request.cookies.get("mca_remember")
        if token:
            us = UserSession.query.filter_by(token=token).first()
            if us and not us.is_expired and us.user and us.user.is_active:
                user = us.user
                session[SESSION_USER_KEY] = user.id

    g._current_user = user
    return user


def is_authenticated() -> bool:
    return current_user() is not None


# =================================================================
# Login / logout
# =================================================================

def login_user(user: User, *, remember: bool = False) -> str | None:
    """Attach a user to the current session. Optionally issue a remember token."""
    session.permanent = True
    session[SESSION_USER_KEY] = user.id
    user.last_login_at = datetime.utcnow()

    token: str | None = None
    if remember:
        token = UserSession.new_token()
        us = UserSession(
            user_id=user.id,
            token=token,
            user_agent=(request.headers.get("User-Agent") or "")[:500],
            ip_address=(request.remote_addr or "")[:64],
            expires_at=datetime.utcnow() + timedelta(days=REMEMBER_DAYS),
        )
        db.session.add(us)
        session[SESSION_TOKEN_KEY] = token

    db.session.commit()
    g._current_user = user
    return token


def logout_user() -> None:
    """Clear session and remember-token (if any)."""
    token = session.pop(SESSION_TOKEN_KEY, None)
    if token:
        UserSession.query.filter_by(token=token).delete()
        db.session.commit()
    session.pop(SESSION_USER_KEY, None)
    if hasattr(g, "_current_user"):
        delattr(g, "_current_user")


# =================================================================
# Decorators
# =================================================================

def _wants_json() -> bool:
    return (
        request.is_json
        or request.path.startswith("/api/")
        or "application/json" in (request.headers.get("Accept") or "")
    )


def login_required(view):
    """Require any authenticated user (any role)."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            if _wants_json():
                return jsonify({"error": "authentication_required"}), 401
            session["next_url"] = request.url
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Require the current user to have one of the listed roles."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                if _wants_json():
                    return jsonify({"error": "authentication_required"}), 401
                session["next_url"] = request.url
                return redirect(url_for("auth.login"))
            if user.role not in roles:
                if _wants_json():
                    return jsonify({"error": "forbidden", "required_role": list(roles)}), 403
                flash("Brak uprawnień do tej akcji.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapper
    return decorator


admin_required = role_required(ROLE_ADMIN)
editor_required = role_required(ROLE_ADMIN, ROLE_EDITOR)


# Backwards-compatibility shim: many existing routes use @require_admin_login.
# Keep the name working so we don't have to touch ~200 endpoints in this PR.
def require_admin_login(view):
    """Legacy alias. Treats the old 'admin' single-user as 'any logged-in user'."""
    return login_required(view)


# =================================================================
# Auth blueprint routes (login, logout, profile)
# =================================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = (request.form.get("identifier") or request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        user = (
            User.query.filter(
                (User.username == identifier) | (User.email == identifier.lower())
            )
            .first()
        )

        if user and user.is_active and user.check_password(password):
            login_user(user, remember=remember)
            next_url = session.pop("next_url", None) or url_for("dashboard")
            return redirect(next_url)

        flash("Nieprawidłowe dane logowania lub konto nieaktywne.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Wylogowano pomyślnie.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html", user=current_user())


@auth_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    user = current_user()
    user.full_name = (request.form.get("full_name") or "").strip() or user.full_name
    user.email = (request.form.get("email") or user.email).strip().lower()
    new_password = (request.form.get("new_password") or "").strip()
    current_password = request.form.get("current_password") or ""

    if new_password:
        if not user.check_password(current_password):
            flash("Aktualne hasło jest nieprawidłowe.", "danger")
            return redirect(url_for("auth.profile"))
        if len(new_password) < 8:
            flash("Nowe hasło musi mieć minimum 8 znaków.", "warning")
            return redirect(url_for("auth.profile"))
        user.set_password(new_password)

    db.session.commit()
    flash("Profil zaktualizowany.", "success")
    return redirect(url_for("auth.profile"))


# =================================================================
# Admin: user management
# =================================================================

@auth_bp.route("/users")
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("auth/users.html", users=users, valid_roles=VALID_ROLES)


@auth_bp.route("/users/create", methods=["POST"])
@admin_required
def create_user():
    email = (request.form.get("email") or "").strip().lower()
    username = (request.form.get("username") or "").strip()
    full_name = (request.form.get("full_name") or "").strip()
    role = request.form.get("role") or ROLE_VIEWER
    password = request.form.get("password") or ""

    if role not in VALID_ROLES:
        flash("Nieprawidłowa rola.", "danger")
        return redirect(url_for("auth.list_users"))

    if not email or not username or len(password) < 8:
        flash("Email, login i hasło (min. 8 znaków) są wymagane.", "warning")
        return redirect(url_for("auth.list_users"))

    if User.query.filter((User.email == email) | (User.username == username)).first():
        flash("Użytkownik z takim emailem lub loginem już istnieje.", "warning")
        return redirect(url_for("auth.list_users"))

    user = User(
        email=email, username=username, full_name=full_name, role=role, is_active=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f"Utworzono użytkownika {username}.", "success")
    return redirect(url_for("auth.list_users"))


@auth_bp.route("/users/<int:user_id>/update", methods=["POST"])
@admin_required
def update_user(user_id: int):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")
    if new_role and new_role in VALID_ROLES:
        user.role = new_role
    user.is_active = bool(request.form.get("is_active"))
    user.full_name = (request.form.get("full_name") or user.full_name).strip()

    new_password = request.form.get("new_password")
    if new_password and len(new_password) >= 8:
        user.set_password(new_password)

    db.session.commit()
    flash("Zaktualizowano użytkownika.", "success")
    return redirect(url_for("auth.list_users"))


@auth_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id: int):
    user = User.query.get_or_404(user_id)
    me = current_user()
    if me and user.id == me.id:
        flash("Nie możesz usunąć własnego konta.", "warning")
        return redirect(url_for("auth.list_users"))
    db.session.delete(user)
    db.session.commit()
    flash("Użytkownik usunięty.", "success")
    return redirect(url_for("auth.list_users"))
