# Replit Auth integration for Blog Automation Agent
import jwt
import os
import uuid
from functools import wraps
from urllib.parse import urlencode

# Allow HTTP for development (required for OAuth2)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import g, session, redirect, request, render_template, url_for
from flask_dance.consumer import (
    OAuth2ConsumerBlueprint,
    oauth_authorized,
    oauth_error,
)
from flask_dance.consumer.storage import BaseStorage
from flask_login import LoginManager, login_user, logout_user, current_user
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from sqlalchemy.exc import NoResultFound
from werkzeug.local import LocalProxy

from app import app, db
from models import OAuth, User

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "replit_auth.login"
login_manager.login_message = "Musisz się zalogować, aby uzyskać dostęp do tego systemu."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(user_id)

class UserSessionStorage(BaseStorage):
    """Custom storage for OAuth tokens per user session"""
    
    def get(self, blueprint):
        """Get OAuth token for current user"""
        try:
            oauth_record = db.session.query(OAuth).filter_by(
                user_id=current_user.get_id(),
                browser_session_key=g.browser_session_key,
                provider=blueprint.name,
            ).one()
            return oauth_record.token
        except (NoResultFound, AttributeError):
            return None

    def set(self, blueprint, token):
        """Set OAuth token for current user"""
        # Delete existing tokens for this user/session/provider
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name,
        ).delete()
        
        # Create new token record
        new_model = OAuth()
        new_model.user_id = current_user.get_id()
        new_model.browser_session_key = g.browser_session_key
        new_model.provider = blueprint.name
        new_model.token = token
        db.session.add(new_model)
        db.session.commit()

    def delete(self, blueprint):
        """Delete OAuth token for current user"""
        db.session.query(OAuth).filter_by(
            user_id=current_user.get_id(),
            browser_session_key=g.browser_session_key,
            provider=blueprint.name
        ).delete()
        db.session.commit()

def make_replit_blueprint():
    """Create Replit OAuth blueprint"""
    try:
        repl_id = os.environ['REPL_ID']
    except KeyError:
        raise SystemExit("REPL_ID environment variable is required for Replit Auth")

    issuer_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc")

    replit_bp = OAuth2ConsumerBlueprint(
        "replit_auth",
        __name__,
        client_id=repl_id,
        client_secret=None,
        base_url=issuer_url,
        authorization_url_params={
            "prompt": "login consent",
        },
        token_url=issuer_url + "/token",
        token_url_params={
            "auth": (),
            "include_client_id": True,
        },
        auto_refresh_url=issuer_url + "/token",
        auto_refresh_kwargs={
            "client_id": repl_id,
        },
        authorization_url=issuer_url + "/auth",
        use_pkce=True,
        code_challenge_method="S256",
        scope=["openid", "profile", "email", "offline_access"],
        storage=UserSessionStorage(),
    )

    @replit_bp.before_app_request
    def set_applocal_session():
        """Set up session keys for OAuth"""
        if '_browser_session_key' not in session:
            session['_browser_session_key'] = uuid.uuid4().hex
        session.modified = True
        g.browser_session_key = session['_browser_session_key']
        g.flask_dance_replit = replit_bp.session

    @replit_bp.route("/logout")
    def logout():
        """Log out the current user"""
        del replit_bp.token
        logout_user()

        # Redirect to Replit logout page
        end_session_endpoint = issuer_url + "/session/end"
        encoded_params = urlencode({
            "client_id": repl_id,
            "post_logout_redirect_uri": request.url_root,
        })
        logout_url = f"{end_session_endpoint}?{encoded_params}"

        return redirect(logout_url)

    @replit_bp.route("/error")
    def error():
        """Handle authentication errors"""
        return render_template("auth_error.html"), 403

    return replit_bp

def save_user(user_claims):
    """Save or update user from OAuth claims"""
    user = User()
    user.id = user_claims['sub']
    user.email = user_claims.get('email')
    user.first_name = user_claims.get('first_name')
    user.last_name = user_claims.get('last_name')
    user.profile_image_url = user_claims.get('profile_image_url')
    
    # Use merge to handle existing users
    merged_user = db.session.merge(user)
    db.session.commit()
    return merged_user

@oauth_authorized.connect
def logged_in(blueprint, token):
    """Handle successful OAuth login"""
    try:
        user_claims = jwt.decode(token['id_token'], options={"verify_signature": False})
        user = save_user(user_claims)
        login_user(user)
        blueprint.token = token
        
        # Redirect to intended page or dashboard
        next_url = session.pop("next_url", None)
        if next_url:
            return redirect(next_url)
        return redirect(url_for('index'))
        
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return redirect(url_for('replit_auth.error'))

@oauth_error.connect
def handle_error(blueprint, error, error_description=None, error_uri=None):
    """Handle OAuth errors"""
    app.logger.error(f"OAuth error: {error} - {error_description}")
    return redirect(url_for('replit_auth.error'))

def require_login(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            session["next_url"] = get_next_navigation_url(request)
            return redirect(url_for('replit_auth.login'))

        # Check if token needs refresh
        if hasattr(replit, 'token') and replit.token:
            expires_in = replit.token.get('expires_in', 0)
            if expires_in < 0:
                refresh_token_url = os.environ.get('ISSUER_URL', "https://replit.com/oidc") + "/token"
                try:
                    token = replit.refresh_token(
                        token_url=refresh_token_url,
                        client_id=os.environ['REPL_ID']
                    )
                    replit.token_updater(token)
                except InvalidGrantError:
                    # Refresh token is invalid, user needs to re-login
                    session["next_url"] = get_next_navigation_url(request)
                    return redirect(url_for('replit_auth.login'))

        return f(*args, **kwargs)
    return decorated_function

def get_next_navigation_url(request):
    """Get the URL to redirect to after login"""
    is_navigation_url = (
        request.headers.get('Sec-Fetch-Mode') == 'navigate' and 
        request.headers.get('Sec-Fetch-Dest') == 'document'
    )
    if is_navigation_url:
        return request.url
    return request.referrer or request.url

# Create proxy for accessing replit session
replit = LocalProxy(lambda: g.flask_dance_replit)

# Create and register the blueprint
replit_auth_blueprint = make_replit_blueprint()