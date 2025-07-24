"""
Simple scheduler module without syntax errors
"""
import logging
import threading
import time
import schedule
import traceback

logger = logging.getLogger(__name__)

# Scheduler thread
scheduler_thread = None
running = False

def start_scheduler():
    """Start the scheduler in a background thread"""
    global scheduler_thread, running
    
    if scheduler_thread and scheduler_thread.is_alive():
        logger.info("Scheduler already running")
        return
    
    logger.info("Starting scheduler")
    running = True
    
    # Schedule tasks
    schedule.every().hour.do(process_content_generation)
    schedule.every().day.at("02:00").do(run_maintenance_tasks)
    
    # Start scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Scheduler started successfully")

def stop_scheduler():
    """Stop the scheduler thread"""
    global running, scheduler_thread
    
    if not running:
        logger.info("Scheduler is not running")
        return
    
    logger.info("Stopping scheduler")
    running = False
    
    # Wait for thread to terminate
    if scheduler_thread:
        scheduler_thread.join(timeout=5)
        scheduler_thread = None

def run_scheduler():
    """Run the scheduler continuously"""
    global running
    
    while running:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            logger.error(traceback.format_exc())
            time.sleep(300)  # Wait 5 minutes after error

def process_content_generation():
    """Process content generation for all active blogs"""
    from app import app, db
    
    with app.app_context():
        try:
            from models import Blog
            
            blogs = Blog.query.filter_by(active=True).all()
            
            if not blogs:
                logger.warning("No active blogs found")
                return
            
            logger.info(f"Processing content generation for {len(blogs)} blogs")
            
            # Simplified processing - just log for now
            for blog in blogs:
                logger.info(f"Processing blog: {blog.name} ({blog.id})")
            
        except Exception as e:
            logger.error(f"Error in content generation: {str(e)}")
            logger.error(traceback.format_exc())

def run_maintenance_tasks():
    """Run maintenance tasks like cleaning up old logs"""
    from app import app, db
    
    with app.app_context():
        try:
            from models import ContentLog
            from datetime import datetime, timedelta
            
            logger.info("Running maintenance tasks")
            
            # Delete old logs beyond retention period (30 days)
            retention_days = 30
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            old_logs = ContentLog.query.filter(
                ContentLog.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            logger.info(f"Deleted {old_logs} old content logs")
            
        except Exception as e:
            logger.error(f"Error in maintenance tasks: {str(e)}")
            logger.error(traceback.format_exc())

def setup_scheduler():
    """Initialize and start the content scheduler"""
    from app import app, db
    
    with app.app_context():
        try:
            from models import Blog
            
            logger.info("Setting up content scheduler")
            
            # Check if there are any active blogs
            active_blogs = Blog.query.filter_by(active=True).count()
            if active_blogs > 0:
                logger.info(f"Found {active_blogs} active blogs, starting scheduler")
                start_scheduler()
            else:
                logger.info("No active blogs found, scheduler will not start")
        
        except Exception as e:
            logger.error(f"Error setting up scheduler: {str(e)}")
            logger.error(traceback.format_exc())