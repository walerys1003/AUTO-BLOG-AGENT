"""
SEO Scheduler

This module provides scheduling functionality for SEO tasks.
"""
import logging
import time
import threading
import schedule
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

def initialize_seo_scheduler():
    """Initialize the SEO scheduler"""
    logger.info("Initializing SEO scheduler")
    
    # Schedule daily SEO analysis
    schedule_daily_seo_analysis()
    
    # Start scheduler thread
    start_scheduler_thread()
    
    logger.info("SEO analysis scheduler initialized and started")
    return True

def schedule_daily_seo_analysis():
    """Schedule daily SEO analysis at 5:00 AM"""
    # Schedule daily analysis at 5:00 AM
    schedule.every().day.at("05:00").do(run_scheduled_seo_analysis)
    
    logger.info("Scheduling daily SEO analysis job at 05:00")
    return True

def start_scheduler_thread():
    """Start the scheduler thread"""
    logger.info("Starting SEO analysis scheduler thread")
    
    # Create and start the scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("SEO analysis scheduler thread started")
    return True

def run_scheduler():
    """Run the scheduler loop"""
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in scheduler loop: {str(e)}")
            time.sleep(60)  # Continue running even if there's an error

def run_scheduled_seo_analysis():
    """Run scheduled SEO analysis for all active blogs"""
    logger.info("Running scheduled SEO analysis")
    
    try:
        from utils.seo.analyzer import run_seo_analysis
        from models import Blog
        from app import db
        
        # Get all active blogs
        with db.app.app_context():
            blogs = Blog.query.filter_by(active=True).all()
            
            if not blogs:
                logger.warning("No active blogs found for scheduled SEO analysis")
                return
            
            # Run analysis for each blog
            for blog in blogs:
                try:
                    # Get blog categories
                    categories = []
                    try:
                        if blog.categories:
                            import json
                            categories = json.loads(blog.categories)
                    except Exception as e:
                        logger.error(f"Error parsing blog categories: {str(e)}")
                        categories = []
                    
                    # Default categories if none specified
                    if not categories:
                        categories = ['biznes', 'technologia', 'zdrowie', 'edukacja', 'rozrywka']
                    
                    # Run analysis
                    logger.info(f"Running scheduled SEO analysis for blog '{blog.name}'")
                    run_seo_analysis(blog.id, categories)
                    
                except Exception as e:
                    logger.error(f"Error running scheduled SEO analysis for blog '{blog.name}': {str(e)}")
                    continue
                
            logger.info("Scheduled SEO analysis completed")
            
    except Exception as e:
        logger.error(f"Error in scheduled SEO analysis: {str(e)}")
    
    return True