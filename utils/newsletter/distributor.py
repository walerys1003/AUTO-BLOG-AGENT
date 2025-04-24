"""
Newsletter distribution system
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

from app import db
from models import Blog, Newsletter, Subscriber, NewsletterConfig
from utils.newsletter.client import EmailOctopusClient

logger = logging.getLogger(__name__)

class NewsletterDistributor:
    """Newsletter distribution system"""
    
    def __init__(self):
        """Initialize newsletter distributor"""
        self.email_clients = {}  # Cache for EmailOctopus clients by blog_id
    
    def get_email_client(self, blog_id: int) -> Optional[EmailOctopusClient]:
        """
        Get or create EmailOctopus client for a blog
        
        Args:
            blog_id: Blog ID
            
        Returns:
            EmailOctopus client instance or None if not configured
        """
        # Return cached client if exists
        if blog_id in self.email_clients:
            return self.email_clients[blog_id]
        
        # Get newsletter configuration
        config = NewsletterConfig.query.filter_by(blog_id=blog_id).first()
        if not config or not config.enabled or not config.email_octopus_api_key:
            logger.error(f"Newsletter not properly configured for blog ID {blog_id}")
            return None
        
        # Create new client
        client = EmailOctopusClient(
            api_key=config.email_octopus_api_key,
            list_id=config.email_octopus_list_id
        )
        
        # Cache and return
        self.email_clients[blog_id] = client
        return client
    
    def send_newsletter(self, newsletter_id: int) -> Dict[str, Any]:
        """
        Send a newsletter to all subscribers
        
        Args:
            newsletter_id: Newsletter ID to send
            
        Returns:
            Result information
        """
        # Get newsletter details
        newsletter = Newsletter.query.get(newsletter_id)
        if not newsletter:
            return {"error": f"Newsletter with ID {newsletter_id} not found"}
        
        # Check status
        if newsletter.status == 'sent':
            return {"error": f"Newsletter has already been sent on {newsletter.sent_at}"}
        
        # Get blog and configuration
        blog_id = newsletter.blog_id
        blog = Blog.query.get(blog_id)
        if not blog:
            return {"error": f"Blog with ID {blog_id} not found"}
        
        config = NewsletterConfig.query.filter_by(blog_id=blog_id).first()
        if not config or not config.enabled:
            return {"error": f"Newsletter not enabled for blog {blog.name}"}
        
        # Get EmailOctopus client
        client = self.get_email_client(blog_id)
        if not client:
            return {"error": f"Could not initialize EmailOctopus client for blog {blog.name}"}
        
        # Prepare campaign parameters
        from_name = config.from_name or blog.name
        from_email = config.from_email
        reply_to = config.reply_to or from_email
        
        if not from_email:
            return {"error": "From email address not configured"}
        
        # Create campaign in EmailOctopus
        campaign_result = client.create_campaign(
            subject=newsletter.subject,
            content_html=newsletter.content_html,
            from_name=from_name,
            from_email=from_email,
            content_text=newsletter.content_text,
            reply_to=reply_to
        )
        
        if "error" in campaign_result:
            logger.error(f"Error creating campaign: {campaign_result['error']}")
            return {"error": f"EmailOctopus API error: {campaign_result['error']}"}
        
        try:
            # Update newsletter status and stats
            newsletter.status = 'sent'
            newsletter.sent_at = datetime.utcnow()
            
            # Store campaign ID for reference
            if 'id' in campaign_result:
                campaign_id = campaign_result['id']
                newsletter.campaign_id = campaign_id
            
            db.session.commit()
            
            logger.info(f"Newsletter '{newsletter.title}' sent successfully")
            return {
                "success": True,
                "newsletter_id": newsletter.id,
                "campaign_id": newsletter.campaign_id if hasattr(newsletter, 'campaign_id') else None
            }
            
        except Exception as e:
            logger.error(f"Error updating newsletter status: {str(e)}")
            return {"error": str(e)}
    
    def process_pending_newsletters(self) -> Dict[str, Any]:
        """
        Process all pending newsletters that are scheduled for now or the past
        
        Returns:
            Results summary
        """
        now = datetime.utcnow()
        
        # Find scheduled newsletters due for sending
        pending_newsletters = Newsletter.query.filter(
            Newsletter.status == 'scheduled',
            Newsletter.scheduled_for <= now
        ).all()
        
        results = {
            "total": len(pending_newsletters),
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        for newsletter in pending_newsletters:
            result = self.send_newsletter(newsletter.id)
            
            if "success" in result and result["success"]:
                results["sent"] += 1
            else:
                results["failed"] += 1
                error_msg = result.get("error", "Unknown error")
                results["errors"].append({
                    "newsletter_id": newsletter.id,
                    "error": error_msg
                })
        
        return results
    
    def upload_subscribers(self, blog_id: int) -> Dict[str, Any]:
        """
        Upload all subscribers for a blog to EmailOctopus
        
        Args:
            blog_id: Blog ID
            
        Returns:
            Result information
        """
        # Get blog and configuration
        blog = Blog.query.get(blog_id)
        if not blog:
            return {"error": f"Blog with ID {blog_id} not found"}
        
        config = NewsletterConfig.query.filter_by(blog_id=blog_id).first()
        if not config or not config.enabled:
            return {"error": f"Newsletter not enabled for blog {blog.name}"}
            
        # Get EmailOctopus client
        client = self.get_email_client(blog_id)
        if not client:
            return {"error": f"Could not initialize EmailOctopus client for blog {blog.name}"}
        
        # Get all active subscribers
        subscribers = Subscriber.query.filter_by(blog_id=blog_id, status='active').all()
        
        results = {
            "total": len(subscribers),
            "added": 0,
            "skipped": 0,
            "failed": 0,
            "errors": []
        }
        
        for subscriber in subscribers:
            # Prepare fields
            fields = {
                "FirstName": subscriber.first_name or "",
                "LastName": subscriber.last_name or ""
            }
            
            # Try to add the subscriber
            result = client.add_subscriber(
                email=subscriber.email,
                fields=fields
            )
            
            if "error" in result:
                if result["error"] == "already_exists":
                    results["skipped"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "email": subscriber.email,
                        "error": result.get("message", "Unknown error")
                    })
            else:
                results["added"] += 1
        
        return results

def create_weekly_newsletter_for_blog(blog_id: int) -> Dict[str, Any]:
    """
    Create a weekly newsletter for a blog and schedule it
    
    Args:
        blog_id: Blog ID
        
    Returns:
        Result information
    """
    from utils.newsletter.generator import NewsletterGenerator
    
    # Get blog and configuration
    blog = Blog.query.get(blog_id)
    if not blog:
        return {"error": f"Blog with ID {blog_id} not found"}
    
    config = NewsletterConfig.query.filter_by(blog_id=blog_id).first()
    if not config or not config.enabled:
        return {"error": f"Newsletter not enabled for blog {blog.name}"}
    
    # Check if weekly scheduling is set
    if config.frequency != 'weekly':
        return {"error": f"Blog {blog.name} is not configured for weekly newsletters"}
    
    # Generate target sending date based on config
    now = datetime.utcnow()
    target_day = config.send_day  # 0-6 for Monday-Sunday
    
    # Calculate next occurrence of the target day
    days_ahead = target_day - now.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
        
    target_date = now + timedelta(days=days_ahead)
    
    # Parse time in HH:MM format
    send_hour, send_minute = map(int, config.send_time.split(':'))
    
    # Set the scheduled time
    scheduled_for = target_date.replace(
        hour=send_hour, 
        minute=send_minute, 
        second=0, 
        microsecond=0
    )
    
    # Create newsletter title and subject
    title = f"{blog.name} Weekly Newsletter - {scheduled_for.strftime('%B %d, %Y')}"
    subject = f"Weekly Update from {blog.name} - {scheduled_for.strftime('%B %d')}"
    
    # Create and schedule newsletter
    generator = NewsletterGenerator(blog_id)
    result = generator.create_scheduled_newsletter(
        title=title,
        subject=subject,
        scheduled_for=scheduled_for,
        days=7,
        article_limit=5
    )
    
    if "success" in result and result["success"]:
        logger.info(f"Weekly newsletter created for {blog.name}, scheduled for {scheduled_for}")
    
    return result