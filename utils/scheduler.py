import logging
import schedule
import threading
import time
import random
from datetime import datetime, timedelta
import json
import traceback
from typing import List, Dict, Any, Optional
from config import Config
from generator.seo import generate_article_topics
from generator.content import generate_article_content
from generator.images import get_featured_image_for_article
from wordpress.publisher import publish_article, check_scheduled_posts, get_optimal_publish_time
from social.autopost import post_article_to_social_media

# Setup logging
logger = logging.getLogger(__name__)

# Global variables for scheduler
running = False
scheduler_thread = None

def start_scheduler():
    """Start the scheduler in a background thread"""
    global running, scheduler_thread
    
    if running:
        logger.warning("Scheduler is already running")
        return
    
    logger.info("Scheduler started")
    running = True
    
    # Set up scheduled tasks
    # Check for pending tasks every hour
    schedule.every(1).hours.do(process_content_generation)
    
    # Check for failed scheduled posts every 2 hours
    schedule.every(2).hours.do(check_scheduled_posts)
    
    # Run maintenance tasks once a day (3 AM UTC)
    schedule.every().day.at("03:00").do(run_maintenance_tasks)
    
    # Start scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

def stop_scheduler():
    """Stop the scheduler thread"""
    global running, scheduler_thread
    
    if not running:
        logger.warning("Scheduler is not running")
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
    try:
        # Import here to avoid circular imports
        from app import db
        from models import Blog, ArticleTopic, ContentLog
        
        # Get all active blogs
        blogs = Blog.query.filter_by(active=True).all()
        
        if not blogs:
            logger.warning("No active blogs found")
            return
        
        logger.info(f"Processing content generation for {len(blogs)} blogs")
        
        # Process each blog
        for blog in blogs:
            try:
                logger.info(f"Processing blog: {blog.name} ({blog.id})")
                
                # Check if we need to generate new topics
                approved_topics = ArticleTopic.query.filter_by(
                    blog_id=blog.id,
                    status="approved"
                ).count()
                
                if approved_topics < 10:
                    logger.info(f"Blog {blog.id} has only {approved_topics} approved topics, generating more")
                    
                    # Generate new topics
                    categories = blog.get_categories()
                    if not categories:
                        categories = ["General", "News", "Guides"]
                    
                    # Generate 15 new topics
                    topics = generate_article_topics(
                        blog_name=blog.name,
                        categories=categories,
                        count=15
                    )
                    
                    # Save topics to database
                    for topic in topics:
                        try:
                            new_topic = ArticleTopic(
                                blog_id=blog.id,
                                title=topic.get('title', ''),
                                category=topic.get('category', categories[0]),
                                status="pending",
                                score=float(topic.get('score', 0.5))
                            )
                            
                            # Set keywords as JSON
                            new_topic.set_keywords(topic.get('keywords', []))
                            
                            db.session.add(new_topic)
                            db.session.commit()
                            logger.info(f"Added new topic: {new_topic.title}")
                        except Exception as e:
                            logger.error(f"Error adding topic: {str(e)}")
                            db.session.rollback()
                
                # Check if we need to publish articles today
                now = datetime.utcnow()
                today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
                
                # Count articles published/scheduled today
                today_articles = ContentLog.query.filter(
                    ContentLog.blog_id == blog.id,
                    ContentLog.created_at >= today_start
                ).count()
                
                # Get configured articles per day
                articles_per_day = Config.ARTICLES_PER_DAY_PER_BLOG
                
                if today_articles >= articles_per_day:
                    logger.info(f"Blog {blog.id} already has {today_articles} articles today (max: {articles_per_day})")
                    continue
                
                # We need to publish more articles
                articles_to_publish = articles_per_day - today_articles
                logger.info(f"Blog {blog.id} needs {articles_to_publish} more articles today")
                
                # Get next approved topics
                topics_to_use = ArticleTopic.query.filter_by(
                    blog_id=blog.id,
                    status="approved"
                ).order_by(
                    ArticleTopic.score.desc()
                ).limit(articles_to_publish).all()
                
                if not topics_to_use:
                    logger.warning(f"No approved topics available for blog {blog.id}")
                    continue
                
                # Process each topic
                for topic in topics_to_use:
                    try:
                        logger.info(f"Creating article from topic: {topic.title}")
                        
                        # Get data from topic
                        title = topic.title
                        keywords = topic.get_keywords()
                        category = topic.category
                        
                        # Generate article content
                        article = generate_article_content(
                            title=title,
                            keywords=keywords,
                            category=category,
                            blog_name=blog.name
                        )
                        
                        if not article:
                            logger.error(f"Failed to generate article for topic {topic.id}")
                            continue
                        
                        # Get featured image
                        featured_image = get_featured_image_for_article(
                            title=title,
                            keywords=keywords
                        )
                        
                        # Publish article
                        success, post_id, error = publish_article(
                            blog_id=blog.id,
                            title=title,
                            content=article.get('content', ''),
                            excerpt=article.get('excerpt', ''),
                            tags=article.get('tags', []),
                            category=category,
                            featured_image=featured_image,
                            schedule=True
                        )
                        
                        if success and post_id:
                            # Update topic status
                            topic.status = "used"
                            db.session.commit()
                            
                            # Check if we should post to social media
                            content_log = ContentLog.query.filter_by(
                                blog_id=blog.id,
                                post_id=post_id
                            ).first()
                            
                            if content_log:
                                # Get article URL from WordPress
                                url = f"{blog.url}/?p={post_id}"
                                
                                # Post to social media
                                social_posts = post_article_to_social_media(
                                    content_log_id=content_log.id,
                                    blog_id=blog.id,
                                    title=title,
                                    excerpt=article.get('excerpt', ''),
                                    url=url,
                                    keywords=keywords,
                                    featured_image=featured_image
                                )
                                
                                if social_posts:
                                    logger.info(f"Posted article to {len(social_posts)} social platforms")
                        else:
                            logger.error(f"Failed to publish article: {error}")
                    
                    except Exception as e:
                        logger.error(f"Error processing topic {topic.id}: {str(e)}")
                        logger.error(traceback.format_exc())
            
            except Exception as e:
                logger.error(f"Error processing blog {blog.id}: {str(e)}")
                logger.error(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Error in content generation: {str(e)}")
        logger.error(traceback.format_exc())

def get_optimal_publish_time(blog_id: int) -> datetime:
    """
    Get the optimal time to publish an article
    
    Args:
        blog_id: ID of the blog
        
    Returns:
        Datetime for optimal publishing
    """
    try:
        # Import here to avoid circular imports
        from app import db
        from models import ContentLog
        
        # Get today's date
        now = datetime.utcnow()
        
        # Get publishing times from config (e.g., "08:00,12:00,16:00,20:00")
        publishing_times = Config.PUBLISHING_TIMES
        
        # Convert to datetime objects for today
        today_slots = []
        for time_str in publishing_times:
            try:
                hour, minute = map(int, time_str.split(':'))
                slot_time = datetime(now.year, now.month, now.day, hour, minute, 0)
                
                # If this time is in the past, skip it
                if slot_time <= now:
                    continue
                    
                today_slots.append(slot_time)
            except:
                continue
        
        # If no valid slots for today, use tomorrow
        if not today_slots:
            tomorrow = now + timedelta(days=1)
            for time_str in publishing_times:
                try:
                    hour, minute = map(int, time_str.split(':'))
                    slot_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour, minute, 0)
                    today_slots.append(slot_time)
                except:
                    continue
        
        # Get already scheduled posts for this blog
        scheduled_times = []
        scheduled_posts = ContentLog.query.filter(
            ContentLog.blog_id == blog_id,
            ContentLog.status == "scheduled",
            ContentLog.published_at > now
        ).all()
        
        for post in scheduled_posts:
            if post.published_at:
                scheduled_times.append(post.published_at)
        
        # Find an available slot
        for slot in sorted(today_slots):
            # Check if this slot is already taken
            taken = False
            for scheduled in scheduled_times:
                # If within 15 minutes of an existing post, consider it taken
                if abs((slot - scheduled).total_seconds()) < 900:  # 15 minutes
                    taken = True
                    break
            
            if not taken:
                return slot
        
        # If all slots are taken, add a random offset to the last slot
        if today_slots:
            last_slot = sorted(today_slots)[-1]
            random_minutes = random.randint(30, 90)  # Add 30-90 minutes
            return last_slot + timedelta(minutes=random_minutes)
        
        # Fallback to 6 hours from now
        return now + timedelta(hours=6)
        
    except Exception as e:
        logger.error(f"Error getting optimal publish time: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Fallback to 6 hours from now
        return datetime.utcnow() + timedelta(hours=6)

def run_maintenance_tasks():
    """Run maintenance tasks like cleaning up old logs"""
    try:
        # Import here to avoid circular imports
        from app import db
        from models import ContentLog
        
        logger.info("Running maintenance tasks")
        
        # Delete old logs beyond retention period
        retention_days = Config.LOG_RETENTION_DAYS
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
    try:
        # Import here to avoid circular imports
        from app import db
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