"""
Script to reset the database and create all tables based on models
Run this when database changes are made or when you need to start fresh
"""

from app import app, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Drops all tables and recreates them"""
    with app.app_context():
        # Import all models to ensure they're registered with SQLAlchemy
        import models  # noqa: F401
        
        logger.info("Dropping all tables...")
        db.drop_all()
        
        logger.info("Creating all tables...")
        db.create_all()
        
        logger.info("Database reset complete!")

if __name__ == "__main__":
    reset_database()