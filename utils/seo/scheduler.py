"""
SEO Analysis Scheduler

Schedules daily SEO analysis and topic generation
"""
import logging
import schedule
import time
import threading
from . import topic_generator

# Setup logging
logger = logging.getLogger(__name__)

def schedule_daily_analysis(time_str="05:00"):
    """
    Schedule daily SEO analysis at specified time
    
    Args:
        time_str: Time to run analysis (24-hour format, e.g. "05:00")
    """
    logger.info(f"Scheduling daily SEO analysis job at {time_str}")
    
    # Schedule the job to run daily at specified time
    schedule.every().day.at(time_str).do(topic_generator.daily_analysis_job)
    
    logger.info("SEO analysis scheduler initialized")

def start_scheduler_thread():
    """
    Start scheduler in a background thread
    
    Returns:
        Thread: Started scheduler thread
    """
    def run_scheduler():
        logger.info("Starting SEO analysis scheduler thread")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    # Create and start thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("SEO analysis scheduler thread started")
    return scheduler_thread

# Initialize scheduler
def init_scheduler():
    """Initialize SEO analysis scheduler"""
    # Schedule daily analysis at 5:00 AM
    schedule_daily_analysis()
    
    # Start scheduler thread
    start_scheduler_thread()
    
    logger.info("SEO analysis scheduler initialized and started")