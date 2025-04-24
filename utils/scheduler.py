import logging
import schedule
import time
import threading
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import Config
from generator.seo import generate_article_topics
from generator.content import generate_article_content
from generator.images import get_featured_image_for_article
from wordpress.publisher import publish_article_to_blog, check_scheduled_posts

# Setup logging
logger = logging.getLogger(__name__)

# Global scheduler object
scheduler_thread = None
is_running = False

def setup_scheduler():
    """
    Set up and start the scheduler for automated content generation and publishing
    """
    global scheduler_thread, is_running
    
    if is_running:
        logger.warning("Scheduler is already running!")
        return
    
    # Set up content generation jobs
    # Run content generation once per day at 00:01
    schedule.every().day.at("00:01").do(generate_content_for_all_blogs)
    
    # Check for scheduled posts every hour
    schedule.every(1).hour.do(check_scheduled_posts)
    
    # Start the scheduler in a separate thread
    is_running = True
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    logger.info("Scheduler started")

def run_scheduler():
    """
    Run the scheduler continuously
    """
    global is_running
    
    while is_running:
        try:
            schedule.run_pending()
            time.sleep(60)  # Sleep for 1 minute between checks
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            logger.error(traceback.format_exc())
            time.sleep(300)  # Sleep longer on error

def stop_scheduler():
    """
    Stop the scheduler
    """
    global is_running
    is_running = False
    
    # Clear all scheduled jobs
    schedule.clear()
    
    logger.info("Scheduler stopped")

def generate_content_for_all_blogs():
    """
    Generate and publish content for all active blogs
    """
    try:
        # Import here to avoid circular imports
        from app import db
        from models import Blog, ArticleTopic
        
        # Get all active blogs
        active_blogs = Blog.query.filter_by(active=True).all()
        logger.info(f"Generating content for {len(active_blogs)} active blogs")
        
        for blog in active_blogs:
            try:
                # Check if we need to generate topics first
                pending_topics = ArticleTopic.query.filter_by(
                    blog_id=blog.id, 
                    status='approved'
                ).count()
                
                if pending_topics < Config.ARTICLES_PER_DAY_PER_BLOG * 2:
                    # Generate new topics if we're running low
                    logger.info(f"Generating new topics for blog {blog.name} (ID: {blog.id})")
                    generate_topics_for_blog(blog.id)
                
                # Get the number of articles to generate for this blog today
                articles_to_generate = Config.ARTICLES_PER_DAY_PER_BLOG
                
                # Generate and publish each article
                for i in range(articles_to_generate):
                    process_blog_content(blog.id)
                    
                    # Sleep to avoid overloading the AI service
                    time.sleep(30)
            
            except Exception as blog_e:
                logger.error(f"Error generating content for blog {blog.id}: {str(blog_e)}")
                logger.error(traceback.format_exc())
                continue
    
    except Exception as e:
        logger.error(f"Error in generate_content_for_all_blogs: {str(e)}")
        logger.error(traceback.format_exc())

def generate_topics_for_blog(blog_id: int, count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate new topics for a blog
    
    Args:
        blog_id: ID of the blog
        count: Number of topics to generate
        
    Returns:
        List of generated topics
    """
    try:
        # Import here to avoid circular imports
        from app import db
        from models import Blog, ArticleTopic
        
        # Get blog data
        blog = Blog.query.get(blog_id)
        if not blog:
            logger.error(f"Blog with ID {blog_id} not found")
            return []
        
        # Get blog categories
        categories = blog.get_categories()
        
        # Generate topics
        topics = generate_article_topics(
            blog_name=blog.name,
            categories=categories,
            count=count
        )
        
        # Save topics to database
        saved_topics = []
        for topic in topics:
            try:
                article_topic = ArticleTopic(
                    blog_id=blog_id,
                    title=topic.get('title', ''),
                    category=topic.get('category', ''),
                    status='pending',
                    score=topic.get('score', 0.0)
                )
                
                # Set keywords
                if 'keywords' in topic:
                    article_topic.set_keywords(topic['keywords'])
                
                db.session.add(article_topic)
                db.session.commit()
                
                # Add to saved topics list
                saved_topics.append({
                    'id': article_topic.id,
                    'title': article_topic.title,
                    'category': article_topic.category,
                    'keywords': article_topic.get_keywords(),
                    'score': article_topic.score
                })
                
            except Exception as topic_e:
                logger.error(f"Error saving topic: {str(topic_e)}")
                db.session.rollback()
                continue
        
        logger.info(f"Generated and saved {len(saved_topics)} topics for blog {blog.name}")
        return saved_topics
    
    except Exception as e:
        logger.error(f"Error generating topics for blog {blog_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def process_blog_content(blog_id: int) -> bool:
    """
    Process content generation and publishing for a single blog
    
    Args:
        blog_id: ID of the blog
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import here to avoid circular imports
        from app import db
        from models import Blog, ArticleTopic
        
        # Get blog data
        blog = Blog.query.get(blog_id)
        if not blog:
            logger.error(f"Blog with ID {blog_id} not found")
            return False
        
        # Get an approved topic
        topic = ArticleTopic.query.filter_by(
            blog_id=blog_id,
            status='approved'
        ).order_by(ArticleTopic.score.desc()).first()
        
        # If no approved topics, try to use a pending one
        if not topic:
            topic = ArticleTopic.query.filter_by(
                blog_id=blog_id,
                status='pending'
            ).order_by(ArticleTopic.score.desc()).first()
        
        # If still no topic, generate some
        if not topic:
            logger.info(f"No topics available for blog {blog.name}, generating new ones")
            new_topics = generate_topics_for_blog(blog_id, count=5)
            
            if new_topics:
                # Get the first generated topic
                topic_id = new_topics[0]['id']
                topic = ArticleTopic.query.get(topic_id)
                
                # Auto-approve this topic since we need it
                topic.status = 'approved'
                db.session.commit()
            else:
                logger.error(f"Failed to generate topics for blog {blog.name}")
                return False
        
        # Generate article content
        try:
            logger.info(f"Generating article for topic: {topic.title}")
            
            article_content = generate_article_content(
                title=topic.title,
                keywords=topic.get_keywords(),
                category=topic.category,
                blog_name=blog.name,
                min_length=Config.ARTICLE_MIN_LENGTH,
                max_length=Config.ARTICLE_MAX_LENGTH
            )
            
            if not article_content or not article_content.get('content'):
                logger.error(f"Failed to generate content for topic {topic.title}")
                return False
            
            # Get featured image
            featured_image = get_featured_image_for_article(topic.title, topic.get_keywords())
            
            # Publish to WordPress
            success, post_id, error = publish_article_to_blog(
                blog_id=blog_id,
                title=topic.title,
                content=article_content,
                featured_image=featured_image,
                schedule=True  # Use scheduling
            )
            
            if success:
                # Mark topic as used
                topic.status = 'used'
                db.session.commit()
                
                logger.info(f"Successfully processed content for blog {blog.name}: {topic.title}")
                return True
            else:
                logger.error(f"Failed to publish article for topic {topic.title}: {error}")
                return False
                
        except Exception as content_e:
            logger.error(f"Error generating content for topic {topic.title}: {str(content_e)}")
            logger.error(traceback.format_exc())
            return False
    
    except Exception as e:
        logger.error(f"Error processing blog content for blog {blog_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return False