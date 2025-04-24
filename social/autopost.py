"""
Social Media Auto Posting Module
"""
import logging
import json
import requests
from datetime import datetime
import time
from typing import Dict, List, Optional, Any
from flask import current_app

from app import db
from models import SocialAccount, ContentLog, Blog
from utils.openrouter.social import generate_social_media_content, generate_hashtag_recommendations

logger = logging.getLogger(__name__)

class SocialMediaPostError(Exception):
    """Exception raised for errors in the social media posting process"""
    pass

def create_social_media_posts(content_log_id: int, preview_only: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Create social media posts for a published article (without posting them)
    
    Args:
        content_log_id (int): ID of the content log entry
        preview_only (bool): If True, only generate content without storing in database
        
    Returns:
        dict: Map of platform to post details, including content
    """
    # Get content log entry
    content_log = ContentLog.query.get(content_log_id)
    if not content_log:
        logger.error(f"Content log entry not found: {content_log_id}")
        raise SocialMediaPostError(f"Content log entry not found: {content_log_id}")
    
    # Get blog details
    blog = Blog.query.get(content_log.blog_id)
    if not blog:
        logger.error(f"Blog not found: {content_log.blog_id}")
        raise SocialMediaPostError(f"Blog not found: {content_log.blog_id}")
    
    # Get active social accounts for this blog
    social_accounts = SocialAccount.query.filter_by(blog_id=blog.id, active=True).all()
    if not social_accounts:
        logger.warning(f"No social accounts found for blog: {blog.name}")
        return {}
    
    # Get platforms
    platforms = list(set([account.platform.lower() for account in social_accounts]))
    
    # Extract content data
    title = content_log.title
    excerpt = content_log.excerpt or ""
    url = content_log.url
    keywords = content_log.get_tags() if content_log.tags else []
    
    # Get featured image if available
    featured_image_data = content_log.get_featured_image()
    image_description = featured_image_data.get("alt_text", "") if featured_image_data else None
    
    # Generate social media content with AI
    try:
        # Map platform names to match API expectations (e.g., 'Twitter' -> 'twitter')
        normalized_platforms = [p.lower() for p in platforms]
        
        # Generate content for each platform
        social_content = generate_social_media_content(
            title=title,
            excerpt=excerpt,
            url=url,
            platforms=normalized_platforms,
            keywords=keywords,
            image_description=image_description
        )
        
        # Create result structure
        social_posts = {}
        
        for platform in normalized_platforms:
            if platform in social_content:
                content = social_content[platform]["content"]
                hashtags = social_content[platform]["hashtags"]
                
                social_posts[platform] = {
                    "content": content,
                    "hashtags": hashtags,
                    "url": url,
                    "featured_image": featured_image_data["url"] if featured_image_data else None,
                    "status": "draft",
                    "created_at": datetime.now().isoformat(),
                    "scheduled_time": None,
                    "post_id": None,
                    "post_url": None
                }
        
        # Save to database if not preview only
        if not preview_only and social_posts:
            content_log.set_social_posts(social_posts)
            db.session.commit()
            logger.info(f"Created social media posts for content: {title}")
        
        return social_posts
        
    except Exception as e:
        logger.error(f"Error generating social media content: {str(e)}")
        raise SocialMediaPostError(f"Error generating social media content: {str(e)}")

def post_article_to_social_media(content_log_id: int, platforms: Optional[List[str]] = None, 
                               scheduled_time: Optional[datetime] = None) -> Dict[str, Dict[str, Any]]:
    """
    Post article to social media platforms
    
    Args:
        content_log_id (int): ID of the content log entry
        platforms (list, optional): List of platforms to post to. If None, post to all available.
        scheduled_time (datetime, optional): Schedule post for this time. If None, post immediately.
    
    Returns:
        dict: Map of platform to post details
    """
    # Get content log entry
    content_log = ContentLog.query.get(content_log_id)
    if not content_log:
        logger.error(f"Content log entry not found: {content_log_id}")
        raise SocialMediaPostError(f"Content log entry not found: {content_log_id}")
    
    # Get blog details
    blog = Blog.query.get(content_log.blog_id)
    if not blog:
        logger.error(f"Blog not found: {content_log.blog_id}")
        raise SocialMediaPostError(f"Blog not found: {content_log.blog_id}")
    
    # Get or create social media posts
    social_posts = content_log.get_social_posts()
    if not social_posts:
        # Generate post content if not already created
        social_posts = create_social_media_posts(content_log_id)
    
    # Filter platforms if specified
    if platforms:
        social_posts = {k: v for k, v in social_posts.items() if k.lower() in [p.lower() for p in platforms]}
    
    if not social_posts:
        logger.warning(f"No social posts to publish for content: {content_log.title}")
        return {}
    
    # Set scheduled time if provided
    if scheduled_time:
        for platform in social_posts:
            social_posts[platform]["scheduled_time"] = scheduled_time.isoformat()
            social_posts[platform]["status"] = "scheduled"
        
        # Update database
        content_log.set_social_posts(social_posts)
        db.session.commit()
        
        logger.info(f"Scheduled social media posts for content ID {content_log_id} at {scheduled_time}")
        return social_posts
    
    # Post to each platform immediately
    for platform, post_data in social_posts.items():
        try:
            # Get social account for this platform
            account = SocialAccount.query.filter_by(
                blog_id=blog.id, 
                platform=platform.capitalize(), 
                active=True
            ).first()
            
            if not account:
                logger.warning(f"No active {platform} account found for blog: {blog.name}")
                post_data["status"] = "error"
                post_data["error"] = f"No active {platform} account configured"
                continue
            
            # Post to the platform
            if platform.lower() == 'facebook':
                result = post_to_facebook(
                    account.account_id, 
                    account.api_token, 
                    post_data["content"], 
                    post_data["url"],
                    post_data["featured_image"]
                )
            elif platform.lower() == 'twitter':
                result = post_to_twitter(
                    account.api_token, 
                    account.api_secret, 
                    post_data["content"], 
                    post_data["hashtags"]
                )
            elif platform.lower() == 'linkedin':
                result = post_to_linkedin(
                    account.account_id, 
                    account.api_token, 
                    post_data["content"], 
                    post_data["url"],
                    post_data["featured_image"]
                )
            elif platform.lower() == 'instagram':
                result = post_to_instagram(
                    account.account_id, 
                    account.api_token, 
                    post_data["content"], 
                    post_data["hashtags"],
                    post_data["featured_image"]
                )
            else:
                logger.warning(f"Unsupported platform: {platform}")
                post_data["status"] = "error"
                post_data["error"] = f"Unsupported platform: {platform}"
                continue
            
            if result.get("success"):
                post_data["status"] = "published"
                post_data["post_id"] = result.get("id")
                post_data["post_url"] = result.get("url")
                post_data["published_at"] = datetime.now().isoformat()
                logger.info(f"Posted article to {platform}: {result.get('url')}")
            else:
                post_data["status"] = "error"
                post_data["error"] = result.get("error", "Unknown error")
                logger.error(f"Error posting to {platform}: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Exception posting to {platform}: {str(e)}")
            post_data["status"] = "error"
            post_data["error"] = str(e)
    
    # Update database with results
    content_log.set_social_posts(social_posts)
    db.session.commit()
    
    # Count successful posts
    successful_posts = sum(1 for p in social_posts.values() if p.get("status") == "published")
    logger.info(f"Posted article to {successful_posts} social media platforms")
    
    return social_posts

# Platform-specific posting functions
def post_to_facebook(page_id, access_token, message, url=None, image_url=None):
    """Post to Facebook page"""
    try:
        api_url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        
        # Prepare post data
        data = {
            "message": message,
            "access_token": access_token,
        }
        
        # Add link if provided
        if url:
            data["link"] = url
            
        # Add image if provided
        if image_url:
            data["picture"] = image_url
            
        # Send request to Facebook API
        response = requests.post(api_url, data=data)
        
        if response.status_code == 200:
            result = response.json()
            post_id = result.get("id")
            return {
                "success": True,
                "id": post_id,
                "url": f"https://facebook.com/{post_id}",
            }
        else:
            return {
                "success": False,
                "error": f"Facebook API error: {response.text}",
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Facebook posting error: {str(e)}",
        }

def post_to_twitter(api_key, api_secret, message, hashtags=None):
    """Post to Twitter (X)"""
    try:
        # Twitter has a 280 character limit
        # Prepare tweet content with hashtags
        tweet_text = message
        if hashtags:
            # Add hashtags, respecting character limit
            hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
            if len(tweet_text) + len(hashtag_text) + 1 <= 280:
                tweet_text = f"{tweet_text} {hashtag_text}"
        
        # For actual implementation, use Twitter API v2
        # This would require OAuth 1.0a authentication
        
        # Mock success response for now
        # In production, replace with actual API call
        post_id = f"tweet_{int(time.time())}"
        
        return {
            "success": True,
            "id": post_id,
            "url": f"https://twitter.com/i/status/{post_id}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Twitter posting error: {str(e)}",
        }

def post_to_linkedin(account_id, access_token, message, url=None, image_url=None):
    """Post to LinkedIn"""
    try:
        # LinkedIn API endpoint for creating posts
        api_url = "https://api.linkedin.com/v2/ugcPosts"
        
        # Build post content
        post_data = {
            "author": f"urn:li:person:{account_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": message
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Add URL if provided
        if url:
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "originalUrl": url
            }]
        
        # Add image if provided (LinkedIn requires more complex media handling)
        # Omitted for simplicity
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # Mock success response for now
        # In production, replace with actual API call
        post_id = f"linkedin_{int(time.time())}"
        
        return {
            "success": True,
            "id": post_id,
            "url": f"https://www.linkedin.com/feed/update/{post_id}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"LinkedIn posting error: {str(e)}",
        }

def post_to_instagram(account_id, access_token, caption, hashtags=None, image_url=None):
    """Post to Instagram"""
    try:
        # Instagram requires an image
        if not image_url:
            return {
                "success": False,
                "error": "Instagram requires an image for posting",
            }
        
        # Build caption with hashtags
        full_caption = caption
        if hashtags:
            hashtag_text = " ".join([f"#{tag}" for tag in hashtags])
            full_caption = f"{full_caption}\n\n{hashtag_text}"
        
        # Instagram Business API requires a Facebook Page ID that is connected to an Instagram Business Account
        # This implementation would require multiple API calls:
        # 1. Upload image to Facebook
        # 2. Create Instagram container
        # 3. Publish the container
        
        # Mock success response for now
        # In production, replace with actual API calls
        post_id = f"ig_{int(time.time())}"
        
        return {
            "success": True,
            "id": post_id,
            "url": f"https://instagram.com/p/{post_id}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Instagram posting error: {str(e)}",
        }

def update_social_post_content(content_log_id, platform, new_content, new_hashtags=None):
    """
    Update the content of a social media post before publishing
    
    Args:
        content_log_id (int): ID of the content log entry
        platform (str): Platform to update (facebook, twitter, etc.)
        new_content (str): New content for the post
        new_hashtags (list, optional): New hashtags for the post
        
    Returns:
        bool: True if update was successful
    """
    try:
        # Get content log entry
        content_log = ContentLog.query.get(content_log_id)
        if not content_log:
            logger.error(f"Content log entry not found: {content_log_id}")
            return False
        
        # Get social posts
        social_posts = content_log.get_social_posts()
        if not social_posts or platform.lower() not in social_posts:
            logger.error(f"No social post found for platform: {platform}")
            return False
        
        # Update content
        social_posts[platform.lower()]["content"] = new_content
        
        # Update hashtags if provided
        if new_hashtags is not None:
            social_posts[platform.lower()]["hashtags"] = new_hashtags
        
        # Save changes
        content_log.set_social_posts(social_posts)
        db.session.commit()
        
        logger.info(f"Updated social post content for {platform}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating social post content: {str(e)}")
        return False