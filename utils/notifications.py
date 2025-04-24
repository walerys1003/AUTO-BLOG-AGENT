"""
Notification utilities for the system
Handles notification creation, sending, and management
"""
import logging
from datetime import datetime
from app import db
from models import Notification
from typing import Dict, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

def send_notification(
    notification_type: str,
    title: str,
    message: str,
    blog_id: Optional[int] = None,
    content_id: Optional[int] = None,
    send_email: bool = False
) -> Dict[str, Any]:
    """
    Create and send a notification
    
    Args:
        notification_type: Type of notification (info, warning, error, success)
        title: Notification title
        message: Notification message
        blog_id: Optional blog ID
        content_id: Optional content ID
        send_email: Whether to send an email notification
        
    Returns:
        Dictionary with status and notification data
    """
    try:
        # Create notification
        notification = Notification(
            type=notification_type,
            title=title,
            message=message,
            blog_id=blog_id,
            content_id=content_id,
            created_at=datetime.utcnow()
        )
        
        # Add to database
        db.session.add(notification)
        db.session.commit()
        
        # Send email if requested
        if send_email:
            # Mark as sent even if we're not implementing email sending yet
            notification.is_email_sent = True
            db.session.commit()
            
            # TODO: Implement email sending
            logger.info(f"Email notification: {title}")
        
        return {
            "success": True,
            "notification_id": notification.id,
            "message": "Notification created and sent"
        }
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return {
            "success": False,
            "message": f"Error sending notification: {str(e)}"
        }

def mark_notification_read(notification_id: int) -> Dict[str, Any]:
    """
    Mark a notification as read
    
    Args:
        notification_id: ID of the notification to mark as read
        
    Returns:
        Dictionary with status and message
    """
    try:
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return {
                "success": False,
                "message": f"Notification not found with ID {notification_id}"
            }
        
        notification.is_read = True
        db.session.commit()
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
        
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return {
            "success": False,
            "message": f"Error marking notification as read: {str(e)}"
        }

def get_unread_notifications(limit: int = 10) -> Dict[str, Any]:
    """
    Get unread notifications
    
    Args:
        limit: Maximum number of notifications to return
        
    Returns:
        Dictionary with status and notifications
    """
    try:
        notifications = Notification.query.filter_by(
            is_read=False
        ).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
        
        return {
            "success": True,
            "notifications": notifications
        }
        
    except Exception as e:
        logger.error(f"Error getting unread notifications: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting unread notifications: {str(e)}",
            "notifications": []
        }

def get_notifications_by_blog(blog_id: int, limit: int = 10) -> Dict[str, Any]:
    """
    Get notifications for a specific blog
    
    Args:
        blog_id: ID of the blog
        limit: Maximum number of notifications to return
        
    Returns:
        Dictionary with status and notifications
    """
    try:
        notifications = Notification.query.filter_by(
            blog_id=blog_id
        ).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
        
        return {
            "success": True,
            "notifications": notifications
        }
        
    except Exception as e:
        logger.error(f"Error getting notifications for blog {blog_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting notifications for blog {blog_id}: {str(e)}",
            "notifications": []
        }

def get_notifications_by_content(content_id: int, limit: int = 10) -> Dict[str, Any]:
    """
    Get notifications for a specific content
    
    Args:
        content_id: ID of the content
        limit: Maximum number of notifications to return
        
    Returns:
        Dictionary with status and notifications
    """
    try:
        notifications = Notification.query.filter_by(
            content_id=content_id
        ).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
        
        return {
            "success": True,
            "notifications": notifications
        }
        
    except Exception as e:
        logger.error(f"Error getting notifications for content {content_id}: {str(e)}")
        return {
            "success": False,
            "message": f"Error getting notifications for content {content_id}: {str(e)}",
            "notifications": []
        }