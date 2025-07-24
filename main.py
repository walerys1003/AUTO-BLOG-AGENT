from app import app, db
import logging
import os
from routes import register_routes
from utils.scheduler import start_scheduler
from models import Blog, SocialAccount, ContentLog, ScheduledPublication
from utils.seo.analyzer import initialize_seo_module
from utils.automation.scheduler import start_automation_scheduler
from routes_scheduling import scheduling_bp
import routes_multi_blog  # Multi-blog management API endpoints

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Register blueprints
app.register_blueprint(scheduling_bp)

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
    
    # Start automation scheduler for workflow management
    try:
        start_automation_scheduler()
        logger.info("Automation scheduler started")
    except Exception as e:
        logger.error(f"Error starting automation scheduler: {str(e)}")
    
    # Initialize SEO module with Google Trends and SerpAPI
    try:
        initialize_seo_module()
        logger.info("SEO module initialized")
    except Exception as e:
        logger.error(f"Error initializing SEO module: {str(e)}")
    logger.info("Flask application initialized")

if __name__ == "__main__":
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=True)
