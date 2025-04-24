import requests
import logging
import json
import base64
from datetime import datetime, timedelta
import time
from typing import Dict, Any, Optional, List, Tuple
import traceback
from models import Blog, ContentLog
from app import db

# Setup logging
logger = logging.getLogger(__name__)

class WordPressPublisher:
    """
    Class to handle WordPress publishing via the WordPress REST API
    """
    
    def __init__(self, blog: Blog):
        """
        Initialize the WordPress publisher with blog configuration
        
        Args:
            blog: Blog model instance with WordPress configuration
        """
        self.blog = blog
        self.api_url = blog.api_url.rstrip("/")
        self.username = blog.username
        self.api_token = blog.api_token
        self.auth_header = self._get_auth_header()
        
    def _get_auth_header(self) -> Dict[str, str]:
        """
        Create authentication header for WordPress API
        
        Returns:
            Dictionary with Authorization header
        """
        # Basic authentication header
        token = base64.b64encode(f"{self.username}:{self.api_token}".encode()).decode()
        return {"Authorization": f"Basic {token}"}
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get categories from the WordPress blog
        
        Returns:
            List of category dictionaries with id and name
        """
        try:
            url = f"{self.api_url}/wp-json/wp/v2/categories"
            response = requests.get(url, headers=self.auth_header)
            
            if response.status_code == 200:
                categories = response.json()
                return [{"id": cat["id"], "name": cat["name"]} for cat in categories]
            else:
                logger.error(f"Failed to fetch categories: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            return []
    
    def create_post(
        self, 
        title: str, 
        content: str, 
        excerpt: str, 
        featured_media_url: Optional[str] = None,
        meta_description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category_ids: Optional[List[int]] = None,
        status: str = "publish",
        publish_date: Optional[datetime] = None
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Create a new WordPress post
        
        Args:
            title: Post title
            content: Post content (HTML)
            excerpt: Post excerpt
            featured_media_url: URL of featured image
            meta_description: SEO meta description
            tags: List of tags
            category_ids: List of category IDs
            status: Post status (draft, publish, future)
            publish_date: Publication date for scheduled posts
            
        Returns:
            Tuple with (success, post_id, error_message)
        """
        try:
            # Prepare post data
            post_data = {
                "title": title,
                "content": content,
                "excerpt": excerpt,
                "status": status,
            }
            
            # Add categories if provided
            if category_ids:
                post_data["categories"] = category_ids
            
            # Add publish date for scheduled posts
            if publish_date and status == "future":
                post_data["date"] = publish_date.isoformat()
            
            # Add tags (create if they don't exist)
            if tags:
                tag_ids = self._get_or_create_tags(tags)
                if tag_ids:
                    post_data["tags"] = tag_ids
            
            # Add meta description if provided
            if meta_description:
                # Different WordPress setups handle meta differently
                # This approach works with Yoast SEO or similar plugins
                post_data["meta"] = {
                    "_yoast_wpseo_metadesc": meta_description
                }
            
            # Create the post
            url = f"{self.api_url}/wp-json/wp/v2/posts"
            response = requests.post(url, json=post_data, headers=self.auth_header)
            
            if response.status_code in (200, 201):
                post_data = response.json()
                post_id = post_data.get("id")
                
                # If we have a featured image, set it
                if featured_media_url and post_id:
                    self._set_featured_image(post_id, featured_media_url)
                
                logger.info(f"Successfully created post {post_id}")
                return True, post_id, None
            else:
                error_msg = f"Failed to create post: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error creating post: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return False, None, error_msg
    
    def _get_or_create_tags(self, tags: List[str]) -> List[int]:
        """
        Get existing tags or create new ones
        
        Args:
            tags: List of tag names
            
        Returns:
            List of tag IDs
        """
        tag_ids = []
        
        try:
            for tag_name in tags:
                # Try to find existing tag
                url = f"{self.api_url}/wp-json/wp/v2/tags"
                params = {"search": tag_name}
                response = requests.get(url, params=params, headers=self.auth_header)
                
                if response.status_code == 200:
                    existing_tags = response.json()
                    
                    # If tag exists, use its ID
                    found = False
                    for tag in existing_tags:
                        if tag["name"].lower() == tag_name.lower():
                            tag_ids.append(tag["id"])
                            found = True
                            break
                    
                    # If tag doesn't exist, create it
                    if not found:
                        create_response = requests.post(
                            url, 
                            json={"name": tag_name}, 
                            headers=self.auth_header
                        )
                        
                        if create_response.status_code in (200, 201):
                            new_tag = create_response.json()
                            tag_ids.append(new_tag["id"])
            
            return tag_ids
                
        except Exception as e:
            logger.error(f"Error processing tags: {str(e)}")
            return tag_ids  # Return whatever tags we've processed so far
    
    def _set_featured_image(self, post_id: int, image_url: str) -> bool:
        """
        Set featured image for a post by URL
        
        Args:
            post_id: WordPress post ID
            image_url: URL of the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # 1. Create media item from URL
            url = f"{self.api_url}/wp-json/wp/v2/media"
            headers = {**self.auth_header, "Content-Disposition": f"attachment; filename=featured-{post_id}.jpg"}
            
            # Download image and upload to WordPress
            image_response = requests.get(image_url)
            if image_response.status_code != 200:
                logger.error(f"Failed to download image: {image_response.status_code}")
                return False
            
            # Upload image to WordPress
            media_response = requests.post(
                url,
                data=image_response.content,
                headers=headers
            )
            
            if media_response.status_code not in (200, 201):
                logger.error(f"Failed to upload media: {media_response.status_code}, {media_response.text}")
                return False
            
            # Get media ID
            media_id = media_response.json().get("id")
            
            # 2. Set as featured image
            update_url = f"{self.api_url}/wp-json/wp/v2/posts/{post_id}"
            update_response = requests.post(
                update_url,
                json={"featured_media": media_id},
                headers=self.auth_header
            )
            
            if update_response.status_code in (200, 201):
                logger.info(f"Successfully set featured image for post {post_id}")
                return True
            else:
                logger.error(f"Failed to set featured image: {update_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting featured image: {str(e)}")
            logger.error(traceback.format_exc())
            return False

def publish_article_to_blog(
    blog_id: int,
    title: str,
    content: Dict[str, Any],
    image: Dict[str, Any],
    category_id: Optional[int] = None,
    publish_time: Optional[datetime] = None
) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Publish an article to a WordPress blog
    
    Args:
        blog_id: ID of the blog in database
        title: Article title
        content: Article content dictionary with html_content, excerpt, meta_description, tags
        image: Image data dictionary with url
        category_id: Category ID (optional)
        publish_time: Scheduled publish time (optional)
        
    Returns:
        Tuple with (success, post_id, error_message)
    """
    try:
        # Get blog from database
        blog = Blog.query.get(blog_id)
        if not blog:
            error_msg = f"Blog with ID {blog_id} not found"
            logger.error(error_msg)
            return False, None, error_msg
        
        # Initialize WordPress publisher
        publisher = WordPressPublisher(blog)
        
        # Determine post status and publish date
        status = "publish"
        if publish_time:
            now = datetime.utcnow()
            if publish_time > now:
                status = "future"  # Schedule the post
        
        # Prepare category IDs
        category_ids = None
        if category_id:
            category_ids = [category_id]
        
        # Create log entry
        log_entry = ContentLog(
            blog_id=blog_id,
            title=title,
            status="publishing"
        )
        db.session.add(log_entry)
        db.session.commit()
        
        # Publish article
        success, post_id, error = publisher.create_post(
            title=title,
            content=content.get("html_content", ""),
            excerpt=content.get("excerpt", ""),
            featured_media_url=image.get("url"),
            meta_description=content.get("meta_description"),
            tags=content.get("tags"),
            category_ids=category_ids,
            status=status,
            publish_date=publish_time
        )
        
        # Update log entry
        log_entry.post_id = post_id
        if success:
            log_entry.status = "published"
            log_entry.published_at = datetime.utcnow() if status == "publish" else publish_time
        else:
            log_entry.status = "error"
            log_entry.error_message = error
        
        db.session.commit()
        
        return success, post_id, error
        
    except Exception as e:
        error_msg = f"Error in publish_article_to_blog: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Ensure log entry is updated
        try:
            log_entry = ContentLog(
                blog_id=blog_id,
                title=title,
                status="error",
                error_message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()
        except:
            logger.error("Failed to create error log entry")
        
        return False, None, error_msg

def get_optimal_publish_time(blog_id: int, date: Optional[datetime] = None) -> datetime:
    """
    Get the optimal time to publish content for a specific blog
    
    Args:
        blog_id: ID of the blog
        date: Target date (defaults to today)
        
    Returns:
        Datetime object for optimal publishing
    """
    from config import Config
    
    # Get target date (default to today)
    if not date:
        date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get publishing times from config
    publishing_times = Config.PUBLISHING_TIMES
    
    # Check existing publications for this blog on this date
    existing_posts = ContentLog.query.filter(
        ContentLog.blog_id == blog_id,
        ContentLog.published_at >= date,
        ContentLog.published_at < date + timedelta(days=1),
        ContentLog.status == "published"
    ).all()
    
    # Get hours already used
    used_hours = [post.published_at.hour for post in existing_posts if post.published_at]
    
    # Find first available time slot
    for time_str in publishing_times:
        hour, minute = map(int, time_str.split(":"))
        
        if hour not in used_hours:
            return date.replace(hour=hour, minute=minute)
    
    # If all times are used, add to last time plus 1 hour
    last_time = publishing_times[-1]
    last_hour, last_minute = map(int, last_time.split(":"))
    
    return date.replace(hour=last_hour + 1, minute=last_minute)
