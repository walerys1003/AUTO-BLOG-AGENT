import logging
import json
import requests
import base64
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

def publish_article(
    blog_id: int,
    title: str,
    content: str,
    excerpt: str = "",
    tags: List[str] = None,
    category: str = None,
    featured_image: Optional[Dict[str, Any]] = None,
    schedule: bool = False
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Publish an article to WordPress
    
    Args:
        blog_id: ID of the blog
        title: Article title
        content: HTML content
        excerpt: Article excerpt
        tags: List of tags
        category: Article category
        featured_image: Featured image data
        schedule: Whether to schedule for optimal time
        
    Returns:
        Tuple of (success, post_id, error_message)
    """
    try:
        # Import here to avoid circular imports
        from app import db
        from models import Blog, ContentLog
        
        # Get blog
        blog = Blog.query.get(blog_id)
        if not blog:
            error_msg = f"Blog not found: {blog_id}"
            logger.error(error_msg)
            return False, None, error_msg
        
        # Get blog categories
        categories = blog.get_categories()
        category_id = None
        
        # Find category ID
        if category and isinstance(categories, dict):
            for cat_id, cat_name in categories.items():
                if cat_name.lower() == category.lower():
                    category_id = int(cat_id)
                    break
            
            # If category not found, log warning
            if not category_id:
                logger.warning(f"Category not found: {category}")
        
        # Prepare post data
        post_data = {
            "title": title,
            "content": content,
            "status": "draft"  # Initially set as draft, will change later
        }
        
        # Add excerpt if provided
        if excerpt:
            post_data["excerpt"] = excerpt
        
        # Add tags if provided
        if tags:
            post_data["tags"] = tags
        
        # Add category if found
        if category_id:
            post_data["categories"] = [category_id]
        
        # Set up API endpoint
        api_endpoint = f"{blog.api_url}/wp-json/wp/v2/posts"
        
        # Set up authentication
        auth = (blog.username, blog.api_token)
        
        # Upload featured image if available
        featured_image_id = None
        if featured_image and featured_image.get('download_url'):
            try:
                # Download the image
                download_url = featured_image.get('download_url')
                if download_url and isinstance(download_url, str):
                    image_response = requests.get(download_url)
                    if image_response.status_code == 200:
                        # Prepare image data for upload
                        image_data = base64.b64encode(image_response.content).decode('utf-8')
                        
                        # Create a media item
                        media_endpoint = f"{blog.api_url}/wp-json/wp/v2/media"
                        media_headers = {
                            "Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.jpg",
                            "Content-Type": "image/jpeg"
                        }
                        
                        media_response = requests.post(
                            media_endpoint,
                            auth=auth,
                            headers=media_headers,
                            data=image_data
                        )
                        
                        if media_response.status_code in (201, 200):
                            media_data = media_response.json()
                            featured_image_id = media_data.get('id')
                            logger.info(f"Uploaded featured image with ID {featured_image_id}")
                        else:
                            logger.warning(f"Failed to upload featured image: {media_response.status_code}, {media_response.text}")
                else:
                    logger.warning(f"Invalid download URL for featured image: {download_url}")
            except Exception as img_e:
                logger.error(f"Error uploading featured image: {str(img_e)}")
                # Continue without featured image if upload fails
        
        # Add featured image if we have one
        if featured_image_id:
            post_data["featured_media"] = featured_image_id
        
        # Determine publication status and date
        optimal_time = datetime.utcnow()  # Default value
        if schedule:
            optimal_time = get_optimal_publish_time(blog_id)
            post_data["status"] = "future"
            post_data["date"] = optimal_time.strftime('%Y-%m-%dT%H:%M:%S')
            logger.info(f"Scheduling post '{title}' for {optimal_time}")
        else:
            post_data["status"] = "publish"
            logger.info(f"Publishing post '{title}' immediately")
        
        # Create the post
        response = requests.post(
            api_endpoint,
            auth=auth,
            json=post_data
        )
        
        if response.status_code in (201, 200):
            post_data = response.json()
            post_id = post_data.get('id')
            
            # Create content log entry
            log_entry = ContentLog(
                blog_id=blog_id,
                title=title,
                status="scheduled" if schedule else "published",
                post_id=post_id,
                created_at=datetime.utcnow(),
                published_at=optimal_time if schedule else datetime.utcnow()
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info(f"Successfully {'scheduled' if schedule else 'published'} post '{title}' with ID {post_id}")
            return True, post_id, None
        else:
            error_msg = f"Failed to publish post: {response.status_code}, {response.text}"
            logger.error(error_msg)
            
            # Create error log entry
            log_entry = ContentLog(
                blog_id=blog_id,
                title=title,
                status="error",
                error_message=error_msg,
                created_at=datetime.utcnow()
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            return False, None, error_msg
    
    except Exception as e:
        error_msg = f"Error publishing article: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Create error log entry
        try:
            from app import db
            log_entry = ContentLog(
                blog_id=blog_id,
                title=title,
                status="error",
                error_message=error_msg,
                created_at=datetime.utcnow()
            )
            
            db.session.add(log_entry)
            db.session.commit()
        except Exception as log_e:
            logger.error(f"Error creating log entry: {str(log_e)}")
        
        return False, None, error_msg

def check_scheduled_posts():
    """
    Check for posts that were scheduled but failed to publish
    and retry publishing them
    """
    try:
        # Get current time
        now = datetime.utcnow()
        
        # Get posts that should have been published already but are still scheduled
        grace_period = timedelta(minutes=30)  # Give WP some time to handle scheduled posts
        from app import db
        from models import ContentLog, Blog
        
        overdue_posts = ContentLog.query.filter(
            ContentLog.status == 'scheduled',
            ContentLog.published_at < (now - grace_period)
        ).all()
        
        logger.info(f"Found {len(overdue_posts)} overdue scheduled posts")
        
        # For each overdue post, check status and retry if needed
        for post in overdue_posts:
            try:
                blog = Blog.query.get(post.blog_id)
                if not blog:
                    logger.error(f"Blog not found for post {post.id}")
                    continue
                
                # Check post status on WordPress
                api_endpoint = f"{blog.api_url}/wp-json/wp/v2/posts/{post.post_id}"
                auth = (blog.username, blog.api_token)
                
                response = requests.get(api_endpoint, auth=auth)
                
                if response.status_code == 200:
                    wp_post = response.json()
                    wp_status = wp_post.get('status')
                    
                    if wp_status == 'publish':
                        # Post was actually published, update our record
                        post.status = 'published'
                        db.session.commit()
                        logger.info(f"Post {post.id} was already published, updated status")
                    else:
                        # Post wasn't published, retry
                        logger.warning(f"Post {post.id} has WordPress status '{wp_status}', attempting to publish now")
                        
                        # Update to publish immediately
                        update_response = requests.post(
                            api_endpoint,
                            auth=auth,
                            json={"status": "publish"}
                        )
                        
                        if update_response.status_code in (200, 201):
                            post.status = 'published'
                            post.published_at = datetime.utcnow()
                            db.session.commit()
                            logger.info(f"Successfully published overdue post {post.id}")
                        else:
                            logger.error(f"Failed to publish overdue post {post.id}: {update_response.status_code}, {update_response.text}")
                else:
                    logger.error(f"Failed to check post {post.id} status: {response.status_code}, {response.text}")
            
            except Exception as post_e:
                logger.error(f"Error processing overdue post {post.id}: {str(post_e)}")
    
    except Exception as e:
        logger.error(f"Error checking scheduled posts: {str(e)}")
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
            except Exception:
                continue
        
        # If no valid slots for today, use tomorrow
        if not today_slots:
            tomorrow = now + timedelta(days=1)
            for time_str in publishing_times:
                try:
                    hour, minute = map(int, time_str.split(':'))
                    slot_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, hour, minute, 0)
                    today_slots.append(slot_time)
                except Exception:
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
            random_minutes = 30  # Add 30 minutes
            return last_slot + timedelta(minutes=random_minutes)
        
        # Fallback to 6 hours from now
        return now + timedelta(hours=6)
        
    except Exception as e:
        logger.error(f"Error getting optimal publish time: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Fallback to 6 hours from now
        return datetime.utcnow() + timedelta(hours=6)