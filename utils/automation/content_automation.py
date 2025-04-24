"""
Content Automation Utility Module
"""
import json
import logging
import traceback
from datetime import datetime, timedelta
import random
import time

from app import db
from models import Blog, ArticleTopic, ContentLog, AutomationRule, SocialAccount
from utils.writing import content_generator
from utils.social import social_publisher

logger = logging.getLogger(__name__)


def run_content_automation():
    """
    Main function to run the content automation process.
    This should be called by the scheduler.
    """
    logger.info("Starting content automation process")
    
    try:
        # Get all active automation rules
        rules = AutomationRule.query.filter_by(active=True).all()
        
        if not rules:
            logger.info("No active automation rules found")
            return
        
        logger.info(f"Found {len(rules)} active automation rules")
        
        for rule in rules:
            process_automation_rule(rule)
            
    except Exception as e:
        logger.error(f"Error in content automation: {str(e)}")
        logger.error(traceback.format_exc())


def process_automation_rule(rule):
    """
    Process a single automation rule
    
    Args:
        rule (AutomationRule): The automation rule to process
    """
    logger.info(f"Processing automation rule: {rule.name} for blog ID {rule.blog_id}")
    
    try:
        # Get the blog
        blog = Blog.query.get(rule.blog_id)
        
        if not blog or not blog.active:
            logger.warning(f"Blog ID {rule.blog_id} not found or inactive")
            return
        
        # Check if we need to publish today based on publishing days
        current_day = datetime.utcnow().weekday()  # 0 = Monday, 6 = Sunday
        if str(current_day) not in rule.publishing_days.split(','):
            logger.info(f"Not scheduled to publish today (day {current_day}) for rule {rule.name}")
            return
        
        # Check if we've already published enough posts today
        posts_published_today = ContentLog.query.filter(
            ContentLog.blog_id == rule.blog_id,
            ContentLog.status == 'published',
            ContentLog.published_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        if posts_published_today >= rule.posts_per_day:
            logger.info(f"Already published {posts_published_today} posts today (limit: {rule.posts_per_day})")
            return
        
        # Auto-approve topics if needed
        if rule.auto_enable_topics:
            auto_approve_topics(rule)
        
        # Get suitable topics for automatic content generation
        topics = get_eligible_topics(rule)
        
        if not topics:
            logger.warning(f"No eligible topics found for rule {rule.name}")
            return
        
        # Process each topic
        posts_to_create = rule.posts_per_day - posts_published_today
        topics_processed = 0
        
        for topic in topics:
            if topics_processed >= posts_to_create:
                break
                
            try:
                generate_and_publish_content(topic, rule)
                topics_processed += 1
                
                # Add a small delay to prevent hammering the APIs
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error processing topic {topic.id}: {str(e)}")
                continue
        
        logger.info(f"Processed {topics_processed} topics for rule {rule.name}")
        
    except Exception as e:
        logger.error(f"Error processing rule {rule.name}: {str(e)}")
        logger.error(traceback.format_exc())


def auto_approve_topics(rule):
    """
    Auto-approve pending topics based on rule criteria
    
    Args:
        rule (AutomationRule): The automation rule
    """
    try:
        # Find pending topics that meet the score threshold
        pending_topics = ArticleTopic.query.filter(
            ArticleTopic.blog_id == rule.blog_id,
            ArticleTopic.status == 'pending',
            ArticleTopic.score >= rule.topic_min_score
        ).all()
        
        if not pending_topics:
            logger.info(f"No pending topics to auto-approve for rule {rule.name}")
            return
        
        for topic in pending_topics:
            topic.status = 'approved'
            logger.info(f"Auto-approved topic: {topic.title} (score: {topic.score})")
        
        db.session.commit()
        logger.info(f"Auto-approved {len(pending_topics)} topics")
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error auto-approving topics: {str(e)}")


def get_eligible_topics(rule):
    """
    Get topics that are eligible for automation based on rule criteria
    
    Args:
        rule (AutomationRule): The automation rule
        
    Returns:
        list: List of eligible ArticleTopic objects
    """
    # Get approved topics that meet the score threshold
    query = ArticleTopic.query.filter(
        ArticleTopic.blog_id == rule.blog_id,
        ArticleTopic.status == 'approved',
        ArticleTopic.score >= rule.topic_min_score
    )
    
    # Filter by categories if specified
    rule_categories = rule.get_categories()
    if rule_categories:
        # This is a simplified approach - in a real system you'd use a more sophisticated query
        topics = query.all()
        filtered_topics = []
        
        for topic in topics:
            if topic.category in rule_categories:
                filtered_topics.append(topic)
        
        # Sort by score (highest first)
        return sorted(filtered_topics, key=lambda t: t.score, reverse=True)
    else:
        # Sort by score (highest first)
        return query.order_by(ArticleTopic.score.desc()).all()


def generate_and_publish_content(topic, rule):
    """
    Generate and publish content for a topic based on rule settings
    
    Args:
        topic (ArticleTopic): The topic to generate content for
        rule (AutomationRule): The automation rule with settings
        
    Returns:
        bool: Success or failure
    """
    logger.info(f"Generating content for topic: {topic.title}")
    
    try:
        # Create a new content log entry
        content_log = ContentLog(
            blog_id=topic.blog_id,
            title=topic.title,
            status='draft',
            created_at=datetime.utcnow()
        )
        
        db.session.add(content_log)
        db.session.commit()
        
        # Generate content using the AI with rule settings
        generation_result = content_generator.generate_article(
            topic=topic.title,
            keywords=topic.get_keywords() if topic.get_keywords() else [],
            style=rule.writing_style,
            length=rule.content_length
        )
        
        content_html = generation_result.get('content', '')
        meta_description = generation_result.get('meta_description', '')
        excerpt = generation_result.get('excerpt', '')
        tags = generation_result.get('tags', [])
        featured_image_url = generation_result.get('featured_image_url', '')
        
        if not content_html:
            logger.error(f"Failed to generate content for topic {topic.id}")
            content_log.status = 'error'
            content_log.error_message = "Failed to generate content"
            db.session.commit()
            return False
        
        # Store the content and metadata in the error_message field temporarily
        # In a production system, there would be a better structure for this
        content_data = {
            'content': content_html,
            'meta_description': meta_description,
            'excerpt': excerpt,
            'tags': tags,
            'featured_image_url': featured_image_url
        }
        
        content_log.error_message = json.dumps(content_data)
        content_log.status = 'ready_to_publish'
        db.session.commit()
        
        # Publish to WordPress
        publish_to_wordpress(content_log, topic)
        
        # Mark the topic as used
        topic.status = 'used'
        db.session.commit()
        
        # If auto-promote is enabled, share to social media
        if rule.auto_promote_content:
            promote_to_social_media(content_log)
        
        logger.info(f"Successfully automated content for topic: {topic.title}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating content for topic {topic.id}: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def publish_to_wordpress(content_log, topic):
    """
    Publish content to WordPress
    
    Args:
        content_log (ContentLog): The content log entry
        topic (ArticleTopic): The topic used for the content
        
    Returns:
        bool: Success or failure
    """
    try:
        # In a real implementation, this would call the WordPress API
        # For now, we'll just mark it as published
        
        # Extract content data
        content_data = json.loads(content_log.error_message)
        
        # TODO: Replace with actual WordPress API integration
        # For now, simulate a successful publication
        post_id = random.randint(1000, 9999)  # Simulate WordPress post ID
        
        content_log.post_id = post_id
        content_log.status = 'published'
        content_log.published_at = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"Published content ID {content_log.id} to WordPress, post ID: {post_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error publishing to WordPress: {str(e)}")
        content_log.status = 'error'
        content_log.error_message = f"Error publishing to WordPress: {str(e)}"
        db.session.commit()
        return False


def promote_to_social_media(content_log):
    """
    Promote published content to social media
    
    Args:
        content_log (ContentLog): The published content log entry
        
    Returns:
        bool: Success or failure
    """
    try:
        # Get social accounts for this blog
        social_accounts = SocialAccount.query.filter_by(
            blog_id=content_log.blog_id,
            active=True
        ).all()
        
        if not social_accounts:
            logger.info(f"No social accounts found for blog ID {content_log.blog_id}")
            return False
        
        # Extract content data for social promotion
        content_data = json.loads(content_log.error_message) if content_log.error_message else {}
        
        # Get blog info
        blog = Blog.query.get(content_log.blog_id)
        
        # Create post URL
        post_url = f"{blog.url}/{content_log.post_id}" if blog and content_log.post_id else None
        
        if not post_url:
            logger.warning(f"Cannot promote content ID {content_log.id} - no post URL")
            return False
        
        # Extract metadata for social posts
        title = content_log.title
        excerpt = content_data.get('excerpt', '')
        featured_image = content_data.get('featured_image_url', '')
        
        # In a real implementation, this would call the social_publisher module
        # For now, we'll just log the attempt
        
        social_posts = {}
        
        for account in social_accounts:
            try:
                # TODO: Replace with actual social media publisher implementation
                # social_post_id = social_publisher.publish_post(account, title, excerpt, post_url, featured_image)
                
                # For now, simulate a successful post
                social_post_id = f"post_{random.randint(1000, 9999)}"
                
                social_posts[account.platform] = {
                    'id': social_post_id,
                    'url': f"https://{account.platform}.com/{account.name}/status/{social_post_id}"
                }
                
                logger.info(f"Posted to {account.platform} for content ID {content_log.id}")
                
            except Exception as e:
                logger.error(f"Error posting to {account.platform}: {str(e)}")
                
        # Store social post information
        if social_posts:
            if hasattr(content_log, 'set_social_posts'):
                content_log.set_social_posts(social_posts)
            elif hasattr(content_log, 'social_media_posts'):
                content_log.social_media_posts = json.dumps(social_posts)
            db.session.commit()
            
        return True
        
    except Exception as e:
        logger.error(f"Error promoting to social media: {str(e)}")
        return False