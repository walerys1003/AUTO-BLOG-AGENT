import os
import logging
import requests
import json
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import traceback
from config import Config
from models import Blog, ContentLog
from generator.images import get_featured_image_for_article
import base64

# Setup logging
logger = logging.getLogger(__name__)

def get_optimal_publish_time(blog_id: int) -> datetime:
    """
    Calculate optimal time to publish a post
    
    Args:
        blog_id: ID of the blog
        
    Returns:
        Datetime object for scheduled publishing
    """
    try:
        # Get current time
        now = datetime.utcnow()
        
        # Get publishing times from config
        publishing_times = Config.PUBLISHING_TIMES
        
        # Get existing scheduled posts for today
        from app import db
        from models import ContentLog
        
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        scheduled_posts = ContentLog.query.filter(
            ContentLog.blog_id == blog_id,
            ContentLog.status == 'scheduled',
            ContentLog.published_at >= today_start,
            ContentLog.published_at < today_end
        ).all()
        
        # Get all scheduled times
        scheduled_times = [post.published_at.strftime('%H:%M') for post in scheduled_posts if post.published_at]
        
        # Find an available time slot
        available_times = [time for time in publishing_times if time not in scheduled_times]
        
        if available_times:
            # Pick the earliest available time that's in the future
            available_times.sort()
            chosen_time = None
            
            for time_str in available_times:
                hours, minutes = map(int, time_str.split(':'))
                potential_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                
                # If the time is in the future, use it
                if potential_time > now:
                    chosen_time = potential_time
                    break
            
            # If no future times available today, schedule for the earliest time tomorrow
            if not chosen_time:
                hours, minutes = map(int, available_times[0].split(':'))
                chosen_time = (now + timedelta(days=1)).replace(hour=hours, minute=minutes, second=0, microsecond=0)
            
            return chosen_time
        else:
            # If all time slots are taken, schedule for tomorrow
            hours, minutes = map(int, publishing_times[0].split(':'))
            return (now + timedelta(days=1)).replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    except Exception as e:
        logger.error(f"Error determining optimal publish time: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Fallback: schedule for 2 hours from now
        return datetime.utcnow() + timedelta(hours=2)

def format_post_content(content: Dict[str, Any], featured_image: Optional[Dict[str, Any]]) -> str:
    """
    Format post content for WordPress
    
    Args:
        content: Article content data
        featured_image: Featured image data
        
    Returns:
        Formatted HTML content
    """
    try:
        html_content = content.get('content', '')
        
        # Add featured image attribution if present
        if featured_image and 'attribution' in featured_image:
            attribution = featured_image['attribution']
            attribution_html = f'<p class="image-attribution">Featured image by <a href="{attribution["url"]}" target="_blank" rel="noopener noreferrer">{attribution["name"]}</a></p>'
            html_content += attribution_html
        
        return html_content
        
    except Exception as e:
        logger.error(f"Error formatting post content: {str(e)}")
        logger.error(traceback.format_exc())
        return content.get('content', '')

def publish_article_to_blog(
    blog_id: int, 
    title: str, 
    content: Dict[str, Any], 
    featured_image: Optional[Dict[str, Any]] = None,
    schedule: bool = True
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Publish an article to a WordPress blog
    
    Args:
        blog_id: ID of the blog to publish to
        title: Article title
        content: Article content dictionary
        featured_image: Featured image data
        schedule: Whether to schedule the post or publish immediately
        
    Returns:
        Tuple of (success, post_id, error_message)
    """
    try:
        # Get blog data
        from app import db
        blog = Blog.query.get(blog_id)
        
        if not blog:
            return False, None, f"Blog with ID {blog_id} not found"
        
        # Get featured image if not provided
        if not featured_image and content.get('keywords'):
            featured_image = get_featured_image_for_article(title, content.get('keywords', []))
        
        # Format post content
        formatted_content = format_post_content(content, featured_image)
        
        # Prepare API endpoint
        api_endpoint = f"{blog.api_url}/wp-json/wp/v2/posts"
        
        # Prepare post data
        post_data = {
            "title": title,
            "content": formatted_content,
            "status": "draft",  # Start as draft, will update status later
            "excerpt": content.get('excerpt', ''),
            "categories": [],  # Will be updated with category IDs
            "tags": []  # Will be updated with tag IDs
        }
        
        # Handle categories
        category = content.get('category')
        if category:
            # Here you would map category name to WP category ID
            # For now, just use default category 1 (Uncategorized)
            post_data["categories"] = [1]
        
        # Handle tags
        tags = content.get('tags', [])
        if tags:
            # Here you would create tags if they don't exist
            # For now, we'll skip this as it requires additional API calls
            pass
        
        # Handle metadata (SEO)
        meta = {}
        if content.get('meta_description'):
            meta["_yoast_wpseo_metadesc"] = content.get('meta_description')
            
        if meta:
            post_data["meta"] = meta
        
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
        from models import ContentLog
        
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