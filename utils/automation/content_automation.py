"""
Content Automation Module

This module handles the automatic creation and publishing of content
based on configured automation rules.
"""
import logging
import random
from datetime import datetime, timedelta
import json
import time

from app import db
from models import Blog, ArticleTopic, ContentLog, AutomationRule
from generator.seo import generate_article_topics
from generator.content import generate_article_content
from generator.images import get_featured_image_for_article
from wordpress.publisher import publish_article
from social.autopost import post_article_to_social_media

logger = logging.getLogger(__name__)


def run_content_automation():
    """
    Main function to run content automation process.
    This is called by the scheduler periodically.
    """
    logger.info("Running content automation...")
    
    try:
        # Get all active automation rules
        rules = AutomationRule.query.filter_by(active=True).all()
        
        if not rules:
            logger.info("No active automation rules found")
            return
        
        logger.info(f"Found {len(rules)} active automation rules")
        
        # Process each rule
        for rule in rules:
            try:
                logger.info(f"Processing automation rule: {rule.name} (ID: {rule.id})")
                
                # Check if this rule should run today
                if not _should_run_today(rule):
                    logger.info(f"Rule {rule.id} is not scheduled to run today")
                    continue
                
                # Run the rule
                result = run_rule(rule.id)
                
                if result.get('success'):
                    logger.info(f"Rule {rule.id} executed successfully: {result.get('message')}")
                else:
                    logger.error(f"Rule {rule.id} failed: {result.get('message')}")
                
            except Exception as e:
                logger.error(f"Error processing rule {rule.id}: {str(e)}")
                continue
        
    except Exception as e:
        logger.error(f"Error in content automation: {str(e)}")


def run_rule(rule_id):
    """
    Run a specific automation rule by ID
    
    Args:
        rule_id: ID of the rule to run
        
    Returns:
        dict: Result with success flag and message
    """
    try:
        # Get the rule
        rule = AutomationRule.query.get(rule_id)
        
        if not rule:
            return {'success': False, 'message': f"Rule with ID {rule_id} not found"}
        
        if not rule.active:
            return {'success': False, 'message': f"Rule {rule.name} is not active"}
        
        # Get the blog
        blog = Blog.query.get(rule.blog_id)
        
        if not blog:
            return {'success': False, 'message': f"Blog with ID {rule.blog_id} not found"}
        
        if not blog.active:
            return {'success': False, 'message': f"Blog {blog.name} is not active"}
        
        # Check if we need to generate more topics
        if rule.auto_enable_topics:
            _auto_enable_topics(rule)
        
        # Check if we have enough approved topics
        approved_topics_count = ArticleTopic.query.filter_by(
            blog_id=rule.blog_id,
            status='approved'
        ).count()
        
        if approved_topics_count < rule.posts_per_day:
            logger.warning(f"Not enough approved topics for rule {rule.id} ({approved_topics_count}/{rule.posts_per_day})")
            
            # Generate new topics if needed
            _generate_new_topics(rule, blog)
            
            if rule.auto_enable_topics:
                _auto_enable_topics(rule)
            
            # Check again if we have enough topics
            approved_topics_count = ArticleTopic.query.filter_by(
                blog_id=rule.blog_id,
                status='approved'
            ).count()
            
            if approved_topics_count < rule.posts_per_day:
                return {
                    'success': False, 
                    'message': f"Still not enough approved topics ({approved_topics_count}/{rule.posts_per_day})"
                }
        
        # Get posts already published/scheduled today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_posts = ContentLog.query.filter(
            ContentLog.blog_id == rule.blog_id,
            ContentLog.created_at >= today_start,
            ContentLog.status.in_(['published', 'ready_to_publish'])
        ).count()
        
        # Calculate how many more posts we need to create
        posts_to_create = min(rule.posts_per_day - today_posts, approved_topics_count)
        
        if posts_to_create <= 0:
            return {
                'success': True,
                'message': f"Already reached daily post limit for rule {rule.name} ({today_posts}/{rule.posts_per_day})"
            }
        
        logger.info(f"Creating {posts_to_create} posts for rule {rule.id}")
        
        # Get the topics to use
        query = ArticleTopic.query.filter_by(
            blog_id=rule.blog_id,
            status='approved'
        )
        
        # Filter by categories if specified
        rule_categories = rule.get_categories()
        if rule_categories:
            query = query.filter(ArticleTopic.category.in_(rule_categories))
        
        # Order by score (highest first) and limit to posts_to_create
        topics = query.order_by(db.desc(ArticleTopic.score)).limit(posts_to_create).all()
        
        if not topics:
            return {
                'success': False,
                'message': f"No suitable topics found for rule {rule.name}"
            }
        
        # Create content for each topic
        created_count = 0
        for topic in topics:
            try:
                # Create the content
                result = _create_content_from_topic(rule, topic)
                
                if result.get('success'):
                    created_count += 1
                    # Mark the topic as used
                    topic.status = 'used'
                    db.session.commit()
            except Exception as e:
                logger.error(f"Error creating content for topic {topic.id}: {str(e)}")
                continue
        
        return {
            'success': True,
            'message': f"Created {created_count} out of {posts_to_create} planned posts for rule {rule.name}"
        }
        
    except Exception as e:
        logger.error(f"Error running rule {rule_id}: {str(e)}")
        return {'success': False, 'message': f"Error: {str(e)}"}


def _should_run_today(rule):
    """
    Check if a rule should run today based on its publishing days
    
    Args:
        rule: The AutomationRule to check
        
    Returns:
        bool: True if the rule should run today
    """
    # Get the day of week (0=Monday, 6=Sunday)
    today = datetime.utcnow().weekday()
    
    # Get the publishing days
    publishing_days = rule.get_publishing_days()
    
    return today in publishing_days


def _auto_enable_topics(rule):
    """
    Automatically approve topics that meet the criteria
    
    Args:
        rule: The AutomationRule to apply
    """
    # Get all pending topics for this blog
    pending_topics = ArticleTopic.query.filter_by(
        blog_id=rule.blog_id,
        status='pending'
    ).all()
    
    # Get categories from rule
    rule_categories = rule.get_categories()
    
    # Check each topic
    approved_count = 0
    for topic in pending_topics:
        # Check if the topic meets the minimum score
        if topic.score >= rule.topic_min_score:
            # Check category if specified
            if not rule_categories or topic.category in rule_categories:
                topic.status = 'approved'
                approved_count += 1
    
    if approved_count > 0:
        db.session.commit()
        logger.info(f"Auto-approved {approved_count} topics for rule {rule.id}")


def _generate_new_topics(rule, blog):
    """
    Generate new topics for a blog
    
    Args:
        rule: The AutomationRule to apply
        blog: The Blog to generate topics for
    """
    try:
        # Get blog categories
        categories = blog.get_categories()
        if not categories:
            categories = ["General", "News", "Guides"]
        
        # Get rule categories if specified
        rule_categories = rule.get_categories()
        if rule_categories:
            # Only use categories that are both in blog and rule
            categories = [c for c in categories if c in rule_categories]
        
        # Generate 15 new topics
        topics = generate_article_topics(
            blog_name=blog.name,
            categories=categories,
            count=15
        )
        
        # Save topics to database
        added_count = 0
        for topic in topics:
            try:
                new_topic = ArticleTopic(
                    blog_id=blog.id,
                    title=topic.get('title', ''),
                    category=topic.get('category', categories[0]),
                    status='pending',
                    score=float(topic.get('score', 0.5))
                )
                
                # Set keywords as JSON
                new_topic.set_keywords(topic.get('keywords', []))
                
                db.session.add(new_topic)
                added_count += 1
            except Exception as e:
                logger.error(f"Error adding topic: {str(e)}")
                continue
        
        if added_count > 0:
            db.session.commit()
            logger.info(f"Generated {added_count} new topics for blog {blog.id}")
        
    except Exception as e:
        logger.error(f"Error generating topics: {str(e)}")


def _create_content_from_topic(rule, topic):
    """
    Create content from a topic using the rule settings
    
    Args:
        rule: The AutomationRule to apply
        topic: The ArticleTopic to create content from
        
    Returns:
        dict: Result with success flag and message
    """
    try:
        # Get data from topic
        title = topic.title
        keywords = topic.get_keywords()
        category = topic.category
        
        # Generate content
        article = generate_article_content(
            title=title,
            keywords=keywords,
            category=category,
            blog_name=rule.blog.name
        )
        
        if not article:
            return {
                'success': False,
                'message': f"Failed to generate content for topic {topic.id}"
            }
        
        # Get featured image
        featured_image = get_featured_image_for_article(
            title=title,
            keywords=keywords
        )
        
        # Create content log
        content_log = ContentLog(
            blog_id=rule.blog_id,
            title=title,
            status='ready_to_publish',
            created_at=datetime.utcnow()
        )
        
        # Store the content data
        content_data = {
            'content': article.get('content', ''),
            'meta_description': article.get('meta_description', ''),
            'excerpt': article.get('excerpt', ''),
            'tags': article.get('tags', []),
            'featured_image_url': featured_image
        }
        
        content_log.error_message = json.dumps(content_data)
        
        db.session.add(content_log)
        db.session.commit()
        
        # Publish the content if API connection is available
        success, post_id, error = publish_article(
            blog_id=rule.blog_id,
            title=title,
            content=article.get('content', ''),
            excerpt=article.get('excerpt', ''),
            tags=article.get('tags', []),
            category=category,
            featured_image=featured_image,
            schedule=True
        )
        
        if success and post_id:
            content_log.status = 'published'
            content_log.post_id = post_id
            content_log.published_at = datetime.utcnow()
            db.session.commit()
            
            # Post to social media if enabled
            if rule.auto_promote_content:
                try:
                    # Get article URL from WordPress
                    url = f"{rule.blog.url}/?p={post_id}"
                    
                    # Post to social media
                    social_posts = post_article_to_social_media(
                        content_log_id=content_log.id,
                        blog_id=rule.blog_id,
                        title=title,
                        excerpt=article.get('excerpt', ''),
                        url=url,
                        keywords=keywords,
                        featured_image=featured_image
                    )
                    
                    if social_posts:
                        content_log.set_social_posts(social_posts)
                        db.session.commit()
                        logger.info(f"Posted article to {len(social_posts)} social platforms")
                
                except Exception as e:
                    logger.error(f"Error posting to social media: {str(e)}")
            
            return {
                'success': True,
                'message': f"Content created and published successfully for topic {topic.id}"
            }
        else:
            logger.error(f"Failed to publish article: {error}")
            return {
                'success': False,
                'message': f"Failed to publish content: {error}"
            }
        
    except Exception as e:
        logger.error(f"Error creating content: {str(e)}")
        return {'success': False, 'message': f"Error: {str(e)}"}


def get_automation_logs(rule_id=None, limit=10):
    """
    Get automation logs for a rule or all rules
    
    Args:
        rule_id (int, optional): ID of the rule to get logs for
        limit (int, optional): Maximum number of logs to return
        
    Returns:
        list: List of log dictionaries
    """
    # In a real implementation, this would query an AutomationLog table
    # For now, we'll return a placeholder empty list
    return []