"""
LEGACY COMPATIBILITY SHIM.

The original `admin_auth.py` provided a single-user env-var based system.
It has been replaced by the full DB-backed `auth.py`.

This module re-exports the old API names so that existing imports keep working:
    from admin_auth import require_admin_login, admin_auth, LOGIN_TEMPLATE
"""

from auth import (  # noqa: F401
    require_admin_login,
    login_required,
    admin_required,
    editor_required,
    current_user,
    is_authenticated,
    login_user,
    logout_user,
)


class _AdminAuthShim:
    """Shim mimicking the old AdminAuth singleton."""

    def is_authenticated(self) -> bool:
        return is_authenticated()

    def authenticate(self, username: str, password: str) -> bool:
        from models import User
        user = User.query.filter(
            (User.username == username) | (User.email == username.lower())
        ).first()
        return bool(user and user.is_active and user.check_password(password))

    def login_user(self) -> None:
        # No-op: real login is now done via auth.login_user(user)
        pass

    def logout_user(self) -> None:
        logout_user()


admin_auth = _AdminAuthShim()

# Empty template kept for backwards compatibility - real login lives in
# templates/auth/login.html and is rendered by auth.login route.
LOGIN_TEMPLATE = ""
