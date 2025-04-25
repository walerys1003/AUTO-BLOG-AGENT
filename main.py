from app import app, db
import logging
import os
from routes import register_routes
from utils.scheduler import start_scheduler
from models import Blog, SocialAccount, ContentLog

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Routes are now registered directly in app.py
# register_routes(app)

# Initialize the database function
def initialize_database():
    # Create tables if they don't exist
    db.create_all()
    
    # Check if we have any blogs configured
    if Blog.query.count() == 0:
        logger.info("No blogs found in database. Please add blogs through the dashboard.")

# Initialize the database and start scheduler
with app.app_context():
    initialize_database()
    # Start the scheduler for automated content generation and posting
    start_scheduler()
    logger.info("Flask application initialized")

if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)
