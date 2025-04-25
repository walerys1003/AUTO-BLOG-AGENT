"""
WordPress publishing manager
Handles scheduling, publication, and optimization of WordPress content
"""
import logging
from datetime import datetime, timedelta, time
import random
from typing import Optional, List, Dict, Any, Tuple

from app import db
from models import Blog, ContentLog, PublishingSchedule, AutomationRule
from utils.wordpress.client import publish_wordpress_post, get_wordpress_post, update_wordpress_post

# Setup logging
logger = logging.getLogger(__name__)

def get_optimal_publish_time(blog_id: int) -> time:
    """
    Get the optimal time to publish content based on analytics data or configured times
    
    Args:
        blog_id: ID of the blog
        
    Returns:
        Time object representing the optimal publishing time
    """
    try:
        # Get blog's publishing times
        blog = Blog.query.get(blog_id)
        if not blog:
            raise ValueError(f"Blog with ID {blog_id} not found")
        
        # Check if there's an automation rule for this blog
        rule = AutomationRule.query.filter_by(blog_id=blog_id, active=True).first()
        # Check if there are time slots defined
        if rule and rule.get_time_slots():
            # Use the first time slot from the rule
            time_slots = rule.get_time_slots()
            if time_slots:
                # Assuming time slots are stored as "HH:MM" strings
                time_str = time_slots[0]
                hour, minute = map(int, time_str.split(':'))
                return time(hour=hour, minute=minute)
        
        # Default times if no analytics data is available
        default_times = [
            time(hour=8, minute=0),   # 8:00 AM
            time(hour=12, minute=0),  # 12:00 PM
            time(hour=16, minute=0),  # 4:00 PM
            time(hour=20, minute=0)   # 8:00 PM
        ]
        
        # Choose a random time from the default times
        # In a real system, this could be based on analytics data
        return random.choice(default_times)
        
    except Exception as e:
        logger.error(f"Error determining optimal publish time: {str(e)}")
        # Default to noon if there's an error
        return time(hour=12, minute=0)

def schedule_content_publication(content_id: int, publish_date: Optional[datetime] = None) -> bool:
    """
    Schedule a piece of content for publication
    
    Args:
        content_id: ID of the content to publish
        publish_date: Date and time to publish, if None, will determine optimal time
        
    Returns:
        Success status
    """
    try:
        # Get the content
        content = ContentLog.query.get(content_id)
        if not content:
            logger.error(f"Content with ID {content_id} not found")
            return False
        
        # If no publish date specified, use today/tomorrow at optimal time
        if not publish_date:
            # Get optimal publish time
            publish_time = get_optimal_publish_time(content.blog_id)
            
            # If it's past the optimal time for today, schedule for tomorrow
            now = datetime.now()
            current_time = now.time()
            
            if current_time > publish_time:
                # Schedule for tomorrow
                publish_date = datetime.combine(now.date() + timedelta(days=1), publish_time)
            else:
                # Schedule for today
                publish_date = datetime.combine(now.date(), publish_time)
        
        # Update the content's publish date
        content.publish_date = publish_date
        content.status = 'scheduled'
        
        # Create or update the publishing schedule
        schedule = PublishingSchedule.query.filter_by(content_id=content.id).first()
        if schedule:
            # Update existing schedule
            schedule.publish_date = publish_date.date()
            schedule.publish_time = publish_date.time()
        else:
            # Create new schedule
            schedule = PublishingSchedule(
                blog_id=content.blog_id,
                content_id=content.id,
                publish_date=publish_date.date(),
                publish_time=publish_date.time()
            )
            db.session.add(schedule)
        
        # Save changes
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error scheduling content: {str(e)}")
        return False

def publish_scheduled_content() -> Dict[str, int]:
    """
    Publish all content that is scheduled for publication now or in the past
    This should be called by a scheduled task
    
    Returns:
        Dict with counts of published, failed, and skipped items
    """
    result = {
        'published': 0,
        'failed': 0,
        'skipped': 0
    }
    
    try:
        # Find content scheduled for publication
        now = datetime.now()
        
        # Get all scheduled content with publish date in the past
        scheduled_content = db.session.query(ContentLog).join(
            PublishingSchedule, ContentLog.id == PublishingSchedule.content_id
        ).filter(
            ContentLog.status == 'scheduled',
            db.func.datetime(PublishingSchedule.publish_date, PublishingSchedule.publish_time) <= now
        ).all()
        
        # For each piece of content, publish it
        for content in scheduled_content:
            # Check if blog requires approval
            blog = Blog.query.get(content.blog_id)
            if blog and blog.approval_required:
                # Update status to pending approval
                content.status = 'pending_review'
                result['skipped'] += 1
                continue
            
            # Publish the content
            success, post_id, error = publish_wordpress_post(
                blog_id=content.blog_id,
                title=content.title,
                content=content.content,
                excerpt=content.excerpt,
                post_id=content.post_id if content.post_id else None,
                category_id=content.category_id,
                tags=content.get_tags(),
                featured_image=content.get_featured_image()
            )
            
            if success:
                # Update status
                content.status = 'published'
                content.post_id = post_id
                content.published_at = now
                result['published'] += 1
            else:
                # Update status with error
                content.status = 'failed'
                content.error_message = error
                result['failed'] += 1
        
        # Commit changes
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error publishing scheduled content: {str(e)}")
    
    return result

def immediate_publish_content(content_id: int) -> Tuple[bool, Optional[str]]:
    """
    Immediately publish content regardless of scheduling
    
    Args:
        content_id: ID of the content to publish
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Get the content
        content = ContentLog.query.get(content_id)
        if not content:
            return False, f"Content with ID {content_id} not found"
        
        # Publish the content
        success, post_id, error = publish_wordpress_post(
            blog_id=content.blog_id,
            title=content.title,
            content=content.content,
            excerpt=content.excerpt,
            post_id=content.post_id if content.post_id else None,
            category_id=content.category_id,
            tags=content.get_tags(),
            featured_image=content.get_featured_image()
        )
        
        if success:
            # Update status
            content.status = 'published'
            content.post_id = post_id
            content.published_at = datetime.now()
            
            # Remove from schedule if it was scheduled
            schedule = PublishingSchedule.query.filter_by(content_id=content.id).first()
            if schedule:
                db.session.delete(schedule)
            
            db.session.commit()
            
            return True, None
        else:
            # Update status with error
            content.status = 'failed'
            content.error_message = error
            db.session.commit()
            
            return False, error
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error publishing content: {str(e)}")
        return False, str(e)

def get_pending_publications(blog_id: Optional[int] = None, status: str = 'all') -> List[ContentLog]:
    """
    Get all pending publications
    
    Args:
        blog_id: Optional blog ID to filter by
        status: Filter by status ('scheduled', 'pending_review', 'draft', 'all')
        
    Returns:
        List of content logs
    """
    query = ContentLog.query
    
    # Filter by status
    if status != 'all':
        query = query.filter_by(status=status)
    else:
        # All pending statuses
        query = query.filter(ContentLog.status.in_(['scheduled', 'pending_review', 'draft']))
    
    # Filter by blog if specified
    if blog_id:
        query = query.filter_by(blog_id=blog_id)
    
    # Sort by publish date
    query = query.order_by(ContentLog.publish_date)
    
    return query.all()

def get_published_content(blog_id: Optional[int] = None, limit: int = 10) -> List[ContentLog]:
    """
    Get published content
    
    Args:
        blog_id: Optional blog ID to filter by
        limit: Maximum number of items to return
        
    Returns:
        List of content logs
    """
    query = ContentLog.query.filter_by(status='published')
    
    # Filter by blog if specified
    if blog_id:
        query = query.filter_by(blog_id=blog_id)
    
    # Sort by publish date (most recent first)
    query = query.order_by(ContentLog.published_at.desc())
    
    return query.limit(limit).all()

def get_failed_publications(blog_id: Optional[int] = None, limit: int = 10) -> List[ContentLog]:
    """
    Get failed publications
    
    Args:
        blog_id: Optional blog ID to filter by
        limit: Maximum number of items to return
        
    Returns:
        List of content logs
    """
    query = ContentLog.query.filter_by(status='failed')
    
    # Filter by blog if specified
    if blog_id:
        query = query.filter_by(blog_id=blog_id)
    
    # Sort by publish date
    query = query.order_by(ContentLog.publish_date.desc())
    
    return query.limit(limit).all()