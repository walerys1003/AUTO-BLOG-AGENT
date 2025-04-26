"""
SEO Scheduler

This module provides scheduling functionality for SEO tasks.
"""
import logging
import threading
import time
import schedule
import json
from datetime import datetime, timedelta
from models import ArticleTopic, Blog, db

# Setup logging
logger = logging.getLogger(__name__)

def initialize_seo_scheduler():
    """Initialize the SEO scheduler"""
    logger.info("Initializing SEO scheduler")
    
    # Schedule daily SEO analysis
    schedule_daily_seo_analysis()
    
    # Start the scheduler thread
    start_scheduler_thread()
    
    logger.info("SEO analysis scheduler initialized and started")
    return True

def schedule_daily_seo_analysis():
    """Schedule daily SEO analysis at 5:00 AM"""
    logger.info("Scheduling daily SEO analysis job at 05:00")
    
    # Schedule daily analysis at 5:00 AM
    schedule.every().day.at("05:00").do(run_daily_seo_analysis)

def start_scheduler_thread():
    """Start the scheduler thread"""
    logger.info("Starting SEO analysis scheduler thread")
    
    # Create and start the scheduler thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("SEO analysis scheduler thread started")

def run_scheduler():
    """Run the scheduler loop"""
    logger.info("Running SEO scheduler loop")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in scheduler loop: {str(e)}")
            time.sleep(300)  # Wait 5 minutes on error

def run_daily_seo_analysis():
    """Run daily SEO analysis"""
    logger.info("Running daily SEO analysis")
    
    try:
        # Get all active blogs
        with db.session.no_autoflush:
            blogs = Blog.query.filter_by(active=True).all()
            
            for blog in blogs:
                try:
                    logger.info(f"Running SEO analysis for blog: {blog.name}")
                    
                    # Get trends for this blog
                    from .trends import get_trending_topics
                    trends = get_trending_topics(limit=10)
                    
                    # Generate topics
                    from .topic_generator import generate_topics_from_trends
                    if trends:
                        # Get categories from the blog
                        categories = []
                        if blog.categories:
                            try:
                                categories = json.loads(blog.categories)
                            except:
                                pass
                        
                        # Generate topics for this blog
                        topics = generate_topics_from_trends(
                            trends=trends,
                            categories=categories,
                            blog_id=blog.id,
                            limit=5
                        )
                        
                        logger.info(f"Generated {len(topics)} topics for blog: {blog.name}")
                    else:
                        logger.warning(f"No trends found for blog: {blog.name}")
                
                except Exception as e:
                    logger.error(f"Error in SEO analysis for blog {blog.name}: {str(e)}")
        
        logger.info("Daily SEO analysis completed")
        return True
        
    except Exception as e:
        logger.error(f"Error in daily SEO analysis: {str(e)}")
        return False