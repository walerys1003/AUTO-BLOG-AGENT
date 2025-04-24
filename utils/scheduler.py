import logging
import traceback
from datetime import datetime, timedelta
import time
from threading import Thread
import schedule
from models import Blog, ArticleTopic, ContentLog
from app import app, db
from generator.seo import generate_article_topics
from generator.content import generate_article_content
from generator.images import get_featured_image_for_article
from wordpress.publisher import publish_article_to_blog, get_optimal_publish_time
from social.autopost import post_article_to_social_media
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

def run_scheduler_continuously():
    """Run the scheduler in a continuous loop"""
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            logger.error(traceback.format_exc())
            time.sleep(300)  # Wait 5 minutes if there's an error

def setup_scheduler():
    """Setup scheduled tasks"""
    with app.app_context():
        # Clean old logs daily at 01:00
        schedule.every().day.at("01:00").do(clean_old_logs)
        
        # Generate topics daily at 05:00
        schedule.every().day.at("05:00").do(generate_topics_for_all_blogs)
        
        # Process content creation and publishing hourly
        schedule.every().hour.do(process_content_pipeline)
        
        # Run the scheduler in a separate thread
        scheduler_thread = Thread(target=run_scheduler_continuously, daemon=True)
        scheduler_thread.start()
        
        logger.info("Scheduler started")

def clean_old_logs():
    """Clean logs older than the retention period"""
    try:
        with app.app_context():
            # Get retention period from config
            retention_days = Config.LOG_RETENTION_DAYS
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old logs
            old_logs = ContentLog.query.filter(ContentLog.created_at < cutoff_date).all()
            
            if old_logs:
                for log in old_logs:
                    db.session.delete(log)
                
                db.session.commit()
                logger.info(f"Deleted {len(old_logs)} logs older than {retention_days} days")
            
    except Exception as e:
        logger.error(f"Error cleaning old logs: {str(e)}")
        logger.error(traceback.format_exc())

def generate_topics_for_all_blogs():
    """Generate article topics for all active blogs"""
    try:
        with app.app_context():
            # Get all active blogs
            blogs = Blog.query.filter_by(active=True).all()
            
            if not blogs:
                logger.warning("No active blogs found")
                return
            
            for blog in blogs:
                # Get blog categories
                categories = blog.get_categories()
                
                if not categories:
                    logger.warning(f"No categories found for blog {blog.id}: {blog.name}")
                    
                    # Use default category
                    categories = [{"name": "General", "id": None}]
                
                # Number of articles per category
                articles_per_day = Config.ARTICLES_PER_DAY_PER_BLOG
                articles_per_category = max(1, articles_per_day // len(categories))
                
                # Generate topics for each category
                for category in categories:
                    category_name = category.get("name", "General")
                    category_id = category.get("id")
                    
                    # Generate topics
                    topics = generate_article_topics(
                        category=category_name, 
                        blog_name=blog.name,
                        count=articles_per_category
                    )
                    
                    if topics:
                        # Save topics to database
                        for topic in topics:
                            article_topic = ArticleTopic(
                                blog_id=blog.id,
                                title=topic.get("title", ""),
                                category=category_name,
                                status="pending",
                                score=topic.get("score", 0)
                            )
                            
                            # Set keywords
                            keywords = topic.get("keywords", [])
                            if keywords:
                                article_topic.set_keywords(keywords)
                            
                            db.session.add(article_topic)
                        
                        db.session.commit()
                        logger.info(f"Generated {len(topics)} topics for blog {blog.id}: {blog.name}, category: {category_name}")
                    else:
                        logger.warning(f"Failed to generate topics for blog {blog.id}: {blog.name}, category: {category_name}")
            
    except Exception as e:
        logger.error(f"Error generating topics for blogs: {str(e)}")
        logger.error(traceback.format_exc())

def process_content_pipeline():
    """Process the content creation and publishing pipeline"""
    try:
        with app.app_context():
            # Get all active blogs
            blogs = Blog.query.filter_by(active=True).all()
            
            if not blogs:
                logger.warning("No active blogs found")
                return
            
            for blog in blogs:
                # Process a single article for this blog in this hourly run
                process_blog_content(blog.id)
            
    except Exception as e:
        logger.error(f"Error processing content pipeline: {str(e)}")
        logger.error(traceback.format_exc())

def process_blog_content(blog_id: int):
    """
    Process content creation and publishing for a single blog
    
    Args:
        blog_id: ID of the blog to process
    """
    try:
        # Get blog
        blog = Blog.query.get(blog_id)
        if not blog or not blog.active:
            logger.warning(f"Blog {blog_id} not found or inactive")
            return
        
        # Check if we've already published the max number of articles today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        articles_today = ContentLog.query.filter(
            ContentLog.blog_id == blog_id,
            ContentLog.published_at >= today_start,
            ContentLog.published_at < today_end,
            ContentLog.status == "published"
        ).count()
        
        max_articles = Config.ARTICLES_PER_DAY_PER_BLOG
        
        if articles_today >= max_articles:
            logger.info(f"Blog {blog_id} already has {articles_today} articles published today (max: {max_articles})")
            return
        
        # Get next pending topic
        topic = ArticleTopic.query.filter_by(
            blog_id=blog_id,
            status="pending"
        ).order_by(ArticleTopic.score.desc()).first()
        
        if not topic:
            logger.warning(f"No pending topics found for blog {blog_id}")
            return
        
        # Mark topic as in progress
        topic.status = "in_progress"
        db.session.commit()
        
        try:
            # Get topic details
            title = topic.title
            keywords = topic.get_keywords()
            category = topic.category
            
            # Generate article content
            content = generate_article_content(
                title=title,
                keywords=keywords,
                category=category,
                blog_name=blog.name
            )
            
            if not content:
                logger.error(f"Failed to generate content for topic {topic.id}: {title}")
                topic.status = "error"
                db.session.commit()
                return
            
            # Get featured image
            image = get_featured_image_for_article(title, keywords)
            
            if not image:
                logger.error(f"Failed to get image for topic {topic.id}: {title}")
                image = {
                    "url": f"https://placehold.co/800x450/png?text={title}"
                }
            
            # Get optimal publish time
            publish_time = get_optimal_publish_time(blog_id)
            
            # Publish article
            success, post_id, error = publish_article_to_blog(
                blog_id=blog_id,
                title=title,
                content=content,
                image=image,
                publish_time=publish_time
            )
            
            if success and post_id:
                # Mark topic as used
                topic.status = "used"
                db.session.commit()
                
                # Get post URL
                post_url = f"{blog.url}/?p={post_id}"
                
                # Post to social media
                social_results = post_article_to_social_media(
                    post_id=post_id,
                    title=title,
                    excerpt=content.get("excerpt", ""),
                    url=post_url,
                    blog_id=blog_id,
                    image_url=image.get("url")
                )
                
                logger.info(f"Successfully published article {post_id} for blog {blog_id}")
                logger.info(f"Social media results: {social_results}")
            else:
                logger.error(f"Failed to publish article for blog {blog_id}: {error}")
                topic.status = "error"
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error processing topic {topic.id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            topic.status = "error"
            db.session.commit()
        
    except Exception as e:
        logger.error(f"Error processing blog content for blog {blog_id}: {str(e)}")
        logger.error(traceback.format_exc())
