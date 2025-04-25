"""
Content Automation Module

This module handles the automatic creation and publishing of content
based on configured automation rules.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

from app import db
from models import Blog, AutomationRule, ArticleTopic, ContentLog
from utils.writing import content_generator
from utils.wordpress import client as wp_client
from utils.social import autopost

# Setup logging
logger = logging.getLogger(__name__)


def run_content_automation():
    """
    Main function to run content automation process.
    This is called by the scheduler periodically.
    """
    logger.info("Running content automation...")
    
    # Get all active automation rules
    active_rules = AutomationRule.query.filter_by(is_active=True).all()
    
    for rule in active_rules:
        # Check if the rule should run today
        if not _should_run_today(rule):
            continue
            
        try:
            # Get the blog associated with this rule
            blog = Blog.query.get(rule.blog_id)
            
            if not blog or not blog.active:
                logger.warning(f"Blog {rule.blog_id} not found or inactive, skipping rule {rule.name}")
                continue
            
            # Auto-enable topics if set
            if rule.auto_enable_topics:
                _auto_enable_topics(rule)
            
            # Generate new topics if needed
            _generate_new_topics(rule, blog)
            
            # Get approved topics for this blog that match the rule's criteria
            topics = _get_topics_for_rule(rule)
            
            # Check if we need to create content today
            if len(topics) < rule.posts_per_day:
                logger.info(f"Not enough approved topics for rule {rule.name}, only {len(topics)} available")
                _log_automation_activity(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    action="check_topics",
                    success=False,
                    message=f"Not enough approved topics (only {len(topics)} available)"
                )
                continue
            
            # Create content for the number of posts per day
            posts_created = 0
            for i in range(min(rule.posts_per_day, len(topics))):
                result = _create_content_from_topic(rule, topics[i])
                if result.get('success'):
                    posts_created += 1
            
            _log_automation_activity(
                rule_id=rule.id,
                rule_name=rule.name,
                action="create_content",
                success=True if posts_created > 0 else False,
                message=f"Created {posts_created} posts"
            )
            
        except Exception as e:
            logger.error(f"Error running automation rule {rule.name}: {str(e)}")
            _log_automation_activity(
                rule_id=rule.id,
                rule_name=rule.name,
                action="run_rule",
                success=False,
                message=f"Error: {str(e)}"
            )


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
            return {"success": False, "message": "Rule not found"}
        
        # Get the blog associated with this rule
        blog = Blog.query.get(rule.blog_id)
        
        if not blog or not blog.active:
            return {"success": False, "message": f"Blog {rule.blog_id} not found or inactive"}
        
        # Auto-enable topics if set
        if rule.auto_enable_topics:
            _auto_enable_topics(rule)
        
        # Get approved topics for this blog that match the rule's criteria
        topics = _get_topics_for_rule(rule)
        
        if not topics:
            # Generate new topics
            _generate_new_topics(rule, blog)
            topics = _get_topics_for_rule(rule)
            
            if not topics:
                return {
                    "success": False, 
                    "message": "No approved topics available. New topics were generated but need approval."
                }
        
        # Create content from the first available topic
        result = _create_content_from_topic(rule, topics[0])
        
        if result.get('success'):
            _log_automation_activity(
                rule_id=rule.id,
                rule_name=rule.name,
                action="manual_run",
                success=True,
                message=result.get('message', "Content created and published successfully")
            )
            return {"success": True, "message": "Content created and published successfully"}
        else:
            _log_automation_activity(
                rule_id=rule.id,
                rule_name=rule.name,
                action="manual_run",
                success=False,
                message=result.get('message', "Failed to create content")
            )
            return {"success": False, "message": result.get('message', "Failed to create content")}
            
    except Exception as e:
        logger.error(f"Error running rule {rule_id}: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


def _should_run_today(rule):
    """
    Check if a rule should run today based on its publishing days
    
    Args:
        rule: The AutomationRule to check
        
    Returns:
        bool: True if the rule should run today
    """
    # Convert the publishing days from string to list of integers
    publishing_days = rule.get_publishing_days()
    
    # Get the current day of week (0 = Monday, 6 = Sunday)
    current_day = datetime.now().weekday()
    
    return current_day in publishing_days


def _auto_enable_topics(rule):
    """
    Automatically approve topics that meet the criteria
    
    Args:
        rule: The AutomationRule to apply
    """
    # Get the blog
    blog = Blog.query.get(rule.blog_id)
    if not blog:
        return
    
    # Get categories criteria
    rule_categories = rule.get_categories()
    
    # Find pending topics that meet the score threshold
    query = ArticleTopic.query.filter(
        ArticleTopic.blog_id == rule.blog_id,
        ArticleTopic.status == 'pending',
        ArticleTopic.score >= rule.topic_min_score
    )
    
    # Filter by categories if needed
    if rule_categories:
        query = query.filter(ArticleTopic.category.in_(rule_categories))
    
    # Get the topics
    topics = query.all()
    
    # Auto-approve them
    for topic in topics:
        topic.status = 'approved'
        db.session.add(topic)
    
    try:
        db.session.commit()
        if topics:
            _log_automation_activity(
                rule_id=rule.id,
                rule_name=rule.name,
                action="auto_approve",
                success=True,
                message=f"Auto-approved {len(topics)} topics"
            )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error auto-approving topics: {str(e)}")
        _log_automation_activity(
            rule_id=rule.id,
            rule_name=rule.name,
            action="auto_approve",
            success=False,
            message=f"Error: {str(e)}"
        )


def _generate_new_topics(rule, blog):
    """
    Generate new topics for a blog
    
    Args:
        rule: The AutomationRule to apply
        blog: The Blog to generate topics for
    """
    # In a real implementation, this would use the SEO inspiration module
    # to generate new topic ideas based on trending keywords and industry analysis
    # For now, we'll just log that this would happen
    _log_automation_activity(
        rule_id=rule.id,
        rule_name=rule.name,
        action="generate_topics",
        success=True,
        message="Topic generation would occur here"
    )


def _get_topics_for_rule(rule):
    """
    Get approved topics that match the rule's criteria
    
    Args:
        rule: The AutomationRule to apply
        
    Returns:
        list: List of matching ArticleTopic objects
    """
    # Get categories criteria
    rule_categories = rule.get_categories()
    
    # Create the base query
    query = ArticleTopic.query.filter(
        ArticleTopic.blog_id == rule.blog_id,
        ArticleTopic.status == 'approved',
        ArticleTopic.score >= rule.topic_min_score
    )
    
    # Filter by categories if needed
    if rule_categories:
        query = query.filter(ArticleTopic.category.in_(rule_categories))
    
    # Order by score (highest first)
    query = query.order_by(ArticleTopic.score.desc())
    
    # Return the topics
    return query.all()


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
        # Get the blog
        blog = Blog.query.get(rule.blog_id)
        if not blog:
            return {"success": False, "message": "Blog not found"}
        
        # Create a new content log entry
        content_log = ContentLog(
            blog_id=blog.id,
            title=topic.title,
            status='draft',
            created_at=datetime.utcnow()
        )
        
        db.session.add(content_log)
        db.session.commit()
        
        # Generate content using the topic and rule settings
        # Determine whether to use paragraph-based or word count-based generation
        if rule.use_paragraph_mode and rule.paragraph_count > 0:
            # Use paragraph-based approach
            generation_result = content_generator.generate_article_by_paragraphs(
                topic=topic.title,
                keywords=topic.get_keywords() if topic.get_keywords() else [],
                style=rule.content_tone,
                paragraph_count=rule.paragraph_count
            )
        else:
            # Use traditional word count-based approach
            generation_result = content_generator.generate_article(
                topic=topic.title,
                keywords=topic.get_keywords() if topic.get_keywords() else [],
                style=rule.content_tone,
                length=rule.content_length
            )
        
        # Extract the content data
        content_html = generation_result.get('content', '')
        meta_description = generation_result.get('meta_description', '')
        excerpt = generation_result.get('excerpt', '')
        tags = generation_result.get('tags', [])
        featured_image_url = generation_result.get('featured_image_url', '')
        
        # Save the generated content to the content_log
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
        
        # Publish the content
        # In a real implementation, this would publish to WordPress
        # For now, we'll just mark it as published
        content_log.status = 'published'
        content_log.published_at = datetime.utcnow()
        
        # Mark the topic as used
        topic.status = 'used'
        
        db.session.commit()
        
        # Log the success
        return {"success": True, "message": f"Content created and published for topic: {topic.title}"}
        
    except Exception as e:
        logger.error(f"Error creating content: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


def get_automation_logs(rule_id=None, limit=10):
    """
    Get automation logs for a rule or all rules
    
    Args:
        rule_id (int, optional): ID of the rule to get logs for
        limit (int, optional): Maximum number of logs to return
        
    Returns:
        list: List of log dictionaries
    """
    # In a real implementation, this would fetch logs from a database table
    # For demonstration, we'll return a list of sample logs
    
    # Create a sample log structure
    logs = [
        {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            "rule_id": 1,
            "rule_name": "Daily Tech News",
            "action": "create_content",
            "success": True,
            "message": "Created 2 posts"
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
            "rule_id": 2,
            "rule_name": "Weekly Financial Updates",
            "action": "auto_approve",
            "success": True,
            "message": "Auto-approved 5 topics"
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
            "rule_id": 1,
            "rule_name": "Daily Tech News",
            "action": "create_content",
            "success": False,
            "message": "Not enough approved topics"
        }
    ]
    
    # Filter by rule_id if provided
    if rule_id:
        logs = [log for log in logs if log["rule_id"] == rule_id]
        
    # Return limited number of logs
    return logs[:limit]


def _log_automation_activity(rule_id, rule_name, action, success, message):
    """
    Log automation activity
    
    Args:
        rule_id (int): ID of the automation rule
        rule_name (str): Name of the automation rule
        action (str): Action performed
        success (bool): Whether the action was successful
        message (str): Message describing the result
    """
    # In a real implementation, this would save to a database table
    # For now, we'll just log to the application log
    if success:
        logger.info(f"Automation rule {rule_name} ({rule_id}): {action} - {message}")
    else:
        logger.warning(f"Automation rule {rule_name} ({rule_id}): {action} FAILED - {message}")