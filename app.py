import os
import logging
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import timedelta

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "blogautomationagent_secret")

# Configure the SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///zyga.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the SQLAlchemy extension
db.init_app(app)

# Import and register authentication first
from replit_auth import replit_auth_blueprint
app.register_blueprint(replit_auth_blueprint, url_prefix="/auth")

# Make sessions permanent for better user experience  
from datetime import timedelta as td
app.permanent_session_lifetime = td(days=7)

# Register routes directly here to ensure they're loaded in all circumstances
from routes import register_routes
register_routes(app)

logger.info("Flask application initialized with authentication and routes")
