import requests
import logging
import json
import base64
from typing import Dict, Any, Optional, List, Tuple
import traceback
from datetime import datetime
import time
import random
from models import Blog, SocialAccount, ContentLog
from app import db
from config import Config
from utils.helpers import get_ai_response

# Setup logging
logger = logging.getLogger(__name__)

def generate_social_content(
    title: str, 
    excerpt: str, 
    url: str, 
    blog_name: str,
    platform: str
) -> str:
    """
    Generate social media content based on article information
    
    Args:
        title: Article title
        excerpt: Article excerpt
        url: Article URL
        blog_name: Name of the blog
        platform: Social media platform (facebook, twitter, linkedin, instagram)
        
    Returns:
        Generated social media content
    """
    try:
        # Customize prompt based on platform
        character_limits = {
            "facebook": 500,
            "twitter": 280,
            "linkedin": 700,
            "instagram": 2200
        }
        
        limit = character_limits.get(platform.lower(), 280)
        
        # Build a prompt customized to each platform
        prompt = f"""
        Generate a compelling social media post for {platform.capitalize()} promoting a new blog article.
        
        Article details:
        - Title: {title}
        - Blog: {blog_name}
        - URL: {url}
        - Excerpt: {excerpt}
        
        Requirements:
        - Maximum length: {limit} characters
        - Include the article URL at the end
        - Use appropriate tone for {platform}
        - For Twitter, use relevant hashtags (max 3)
        - For Instagram, use relevant hashtags (5-10)
        - For LinkedIn, use a professional tone and 2-3 relevant hashtags
        - Include a call-to-action
        
        Return just the text of the social media post, ready to publish.
        """
        
        # Get response from AI
        response = get_ai_response(
            prompt=prompt,
            model=Config.DEFAULT_SOCIAL_MODEL
        )
        
        if response:
            # Clean up the response
            content = response.strip()
            
            # Ensure URL is included
            if url not in content:
                content = f"{content}\n\n{url}"
            
            # Ensure length is appropriate
            if len(content) > limit:
                # Truncate and add URL
                content = content[:limit - len(url) - 6] + "...\n\n" + url
            
            return content
        else:
            # Fallback if AI fails
            return generate_fallback_social_content(title, url, platform)
            
    except Exception as e:
        logger.error(f"Error generating social content for {platform}: {str(e)}")
        return generate_fallback_social_content(title, url, platform)

def generate_fallback_social_content(title: str, url: str, platform: str) -> str:
    """
    Generate fallback social media content when AI generation fails
    
    Args:
        title: Article title
        url: Article URL
        platform: Social media platform
        
    Returns:
        Basic social media content
    """
    # Different templates per platform
    templates = {
        "facebook": [
            "📝 New blog post: {title}\n\nCheck it out: {url}",
            "Just published: {title}\n\nRead more: {url}",
            "Fresh content alert! 🔔\n\n{title}\n\nRead the full article: {url}"
        ],
        "twitter": [
            "📝 New post: {title}\n\nCheck it out! {url} #blog #newcontent",
            "Just published! {title}\n\nRead here: {url} #blogging",
            "Fresh content alert! 🔔\n\n{title}\n\n{url} #content #blog"
        ],
        "linkedin": [
            "📝 New article: {title}\n\nI've just published a new article on this topic. Your thoughts?\n\nRead here: {url}",
            "Just published: {title}\n\nI'd appreciate your professional feedback on this topic.\n\n{url}",
            "📋 Fresh insights on {title}\n\nCheck out my latest article and let me know what you think: {url}"
        ],
        "instagram": [
            "📝 New blog post alert!\n\n{title}\n\nLink in bio or head to: {url}\n\n#blog #content #newpost #blogging #writer",
            "Just published a new article: {title}\n\nRead the full post at {url}\n\n#blogger #writing #article #newcontent #blog",
            "Fresh content for you! 🔔\n\n{title}\n\nCheck out the link in my bio or visit: {url}\n\n#contentcreator #blogging #writer #newpost"
        ]
    }
    
    # Get templates for the platform or use default templates
    platform_templates = templates.get(platform.lower(), templates["twitter"])
    
    # Select a random template
    template = random.choice(platform_templates)
    
    # Fill in the template
    content = template.format(title=title, url=url)
    
    return content

class SocialMediaPublisher:
    """Base class for social media publishers"""
    
    def __init__(self, account: SocialAccount):
        self.account = account
        self.platform = account.platform
    
    def publish(self, content: str, image_url: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Publish content to social media
        
        Args:
            content: Content to publish
            image_url: Optional image URL
            
        Returns:
            Tuple with (success, post_url or id, error_message)
        """
        raise NotImplementedError("Subclasses must implement this method")

class FacebookPublisher(SocialMediaPublisher):
    """Facebook publisher using Graph API"""
    
    def publish(self, content: str, image_url: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            # Page ID should be in account_id
            page_id = self.account.account_id
            access_token = self.account.api_token
            
            # API endpoint
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            
            # Prepare data
            data = {
                "message": content,
                "access_token": access_token
            }
            
            # If image URL is provided, include it
            if image_url:
                data["link"] = image_url
            
            # Make API request
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                result = response.json()
                post_id = result.get("id")
                post_url = f"https://facebook.com/{post_id}"
                
                logger.info(f"Successfully posted to Facebook: {post_id}")
                return True, post_url, None
            else:
                error_msg = f"Failed to post to Facebook: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error posting to Facebook: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return False, None, error_msg

class TwitterPublisher(SocialMediaPublisher):
    """Twitter publisher using API v2"""
    
    def publish(self, content: str, image_url: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            api_key = self.account.api_token
            api_secret = self.account.api_secret
            
            # For Twitter API v2, we need to get a bearer token first
            auth_url = "https://api.twitter.com/oauth2/token"
            auth_headers = {
                "Authorization": "Basic " + base64.b64encode(f"{api_key}:{api_secret}".encode()).decode(),
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
            }
            auth_data = {"grant_type": "client_credentials"}
            
            auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)
            
            if auth_response.status_code != 200:
                error_msg = f"Failed to get Twitter bearer token: {auth_response.status_code}, {auth_response.text}"
                logger.error(error_msg)
                return False, None, error_msg
            
            bearer_token = auth_response.json().get("access_token")
            
            # Now post the tweet
            tweet_url = "https://api.twitter.com/2/tweets"
            tweet_headers = {
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json"
            }
            
            tweet_data = {
                "text": content
            }
            
            # If we have an image, we'd need to upload it first and get a media_id
            # This is simplified and would need expanded for actual image uploading
            
            tweet_response = requests.post(tweet_url, headers=tweet_headers, json=tweet_data)
            
            if tweet_response.status_code in (200, 201):
                result = tweet_response.json()
                tweet_id = result.get("data", {}).get("id")
                tweet_url = f"https://twitter.com/i/web/status/{tweet_id}"
                
                logger.info(f"Successfully posted to Twitter: {tweet_id}")
                return True, tweet_url, None
            else:
                error_msg = f"Failed to post to Twitter: {tweet_response.status_code}, {tweet_response.text}"
                logger.error(error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error posting to Twitter: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return False, None, error_msg

class LinkedInPublisher(SocialMediaPublisher):
    """LinkedIn publisher using API"""
    
    def publish(self, content: str, image_url: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            access_token = self.account.api_token
            user_id = self.account.account_id
            
            # API endpoint
            url = "https://api.linkedin.com/v2/ugcPosts"
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Prepare data
            data = {
                "author": f"urn:li:person:{user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # If image URL is provided, include it
            if image_url:
                data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
                data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "originalUrl": image_url
                    }
                ]
            
            # Make API request
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in (200, 201):
                result = response.json()
                post_id = result.get("id")
                
                logger.info(f"Successfully posted to LinkedIn: {post_id}")
                return True, post_id, None
            else:
                error_msg = f"Failed to post to LinkedIn: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error posting to LinkedIn: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return False, None, error_msg

class InstagramPublisher(SocialMediaPublisher):
    """Instagram publisher using Facebook Graph API"""
    
    def publish(self, content: str, image_url: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            # Instagram business account ID
            ig_account_id = self.account.account_id
            access_token = self.account.api_token
            
            # If no image URL, we can't post (Instagram requires an image)
            if not image_url:
                error_msg = "Instagram posts require an image"
                logger.error(error_msg)
                return False, None, error_msg
            
            # 1. First, upload the image to get a container ID
            upload_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media"
            upload_data = {
                "image_url": image_url,
                "caption": content,
                "access_token": access_token
            }
            
            upload_response = requests.post(upload_url, data=upload_data)
            
            if upload_response.status_code != 200:
                error_msg = f"Failed to upload Instagram image: {upload_response.status_code}, {upload_response.text}"
                logger.error(error_msg)
                return False, None, error_msg
            
            container_id = upload_response.json().get("id")
            
            # 2. Publish the container
            publish_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish"
            publish_data = {
                "creation_id": container_id,
                "access_token": access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_data)
            
            if publish_response.status_code == 200:
                result = publish_response.json()
                post_id = result.get("id")
                
                logger.info(f"Successfully posted to Instagram: {post_id}")
                return True, post_id, None
            else:
                error_msg = f"Failed to publish Instagram post: {publish_response.status_code}, {publish_response.text}"
                logger.error(error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error posting to Instagram: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return False, None, error_msg

def get_publisher_for_platform(account: SocialAccount) -> SocialMediaPublisher:
    """
    Get the appropriate publisher for a social media platform
    
    Args:
        account: Social account information
        
    Returns:
        SocialMediaPublisher instance
    """
    platform = account.platform.lower()
    
    publishers = {
        "facebook": FacebookPublisher,
        "twitter": TwitterPublisher,
        "linkedin": LinkedInPublisher,
        "instagram": InstagramPublisher
    }
    
    publisher_class = publishers.get(platform)
    
    if not publisher_class:
        logger.warning(f"Unsupported platform: {platform}, using fallback")
        publisher_class = SocialMediaPublisher
    
    return publisher_class(account)

def post_article_to_social_media(
    post_id: int, 
    title: str, 
    excerpt: str, 
    url: str, 
    blog_id: int,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Post article to all social media accounts for a blog
    
    Args:
        post_id: WordPress post ID
        title: Article title
        excerpt: Article excerpt
        url: Article URL
        blog_id: Blog ID
        image_url: Optional image URL
        
    Returns:
        Dictionary of results by platform
    """
    results = {}
    
    try:
        # Get blog information
        blog = Blog.query.get(blog_id)
        if not blog:
            logger.error(f"Blog with ID {blog_id} not found")
            return {"error": f"Blog with ID {blog_id} not found"}
        
        # Get all active social accounts for this blog
        social_accounts = SocialAccount.query.filter_by(blog_id=blog_id, active=True).all()
        
        if not social_accounts:
            logger.warning(f"No active social accounts found for blog {blog_id}")
            return {"warning": "No active social accounts found"}
        
        # Get content log for this post
        content_log = ContentLog.query.filter_by(blog_id=blog_id, post_id=post_id).first()
        
        # Post to each social media platform
        for account in social_accounts:
            try:
                # Generate content for this platform
                content = generate_social_content(
                    title=title,
                    excerpt=excerpt,
                    url=url,
                    blog_name=blog.name,
                    platform=account.platform
                )
                
                # Get publisher for this platform
                publisher = get_publisher_for_platform(account)
                
                # Publish content
                success, post_url, error = publisher.publish(content, image_url)
                
                results[account.platform] = {
                    "success": success,
                    "post_url": post_url,
                    "error": error
                }
                
                # Add delay between requests to avoid rate limits
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"Error posting to {account.platform}: {str(e)}"
                logger.error(error_msg)
                
                results[account.platform] = {
                    "success": False,
                    "error": error_msg
                }
        
        # Update content log with social media results
        if content_log:
            content_log.set_social_posts(results)
            db.session.commit()
        
        return results
        
    except Exception as e:
        error_msg = f"Error in post_article_to_social_media: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        return {"error": error_msg}
