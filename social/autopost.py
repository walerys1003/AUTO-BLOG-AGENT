import logging
import json
import requests
import os
import base64
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import traceback
from config import Config
from models import Blog, SocialAccount, ContentLog
from utils.helpers import get_ai_response
from generator.images import get_featured_image_for_article

# Setup logging
logger = logging.getLogger(__name__)

def create_social_media_content(
    title: str,
    excerpt: str,
    url: str,
    keywords: List[str],
    featured_image: Optional[Dict[str, Any]] = None,
    platforms: Optional[List[str]] = None
) -> Dict[str, Dict[str, str]]:
    """
    Create social media content for various platforms
    
    Args:
        title: Article title
        excerpt: Article excerpt/summary
        url: Published article URL
        keywords: Article keywords for hashtags
        featured_image: Featured image data
        platforms: List of platforms to create content for
        
    Returns:
        Dictionary of platform-specific content
    """
    try:
        # Default platforms if none specified
        if not platforms:
            platforms = ["facebook", "twitter", "linkedin", "instagram"]
        
        # Create system prompt for social content generation
        system_prompt = """You are a social media marketing expert who creates engaging, platform-specific content to promote blog articles.
Your posts are optimized for each platform's unique audience, format requirements, and engagement patterns.
"""

        # Format keywords into hashtags
        hashtags = []
        for keyword in keywords:
            # Convert multi-word keywords into camelCase hashtags
            if " " in keyword:
                parts = keyword.split()
                hashtag = "#" + parts[0].lower() + "".join(part.capitalize() for part in parts[1:])
                hashtags.append(hashtag)
            else:
                hashtags.append("#" + keyword.lower())
        
        # Limit to 5 most relevant hashtags
        hashtags = hashtags[:5]
        hashtags_text = " ".join(hashtags)
        
        # Construct the prompt
        prompt = f"""Create social media posts to promote a blog article with the following details:

Title: {title}
Excerpt: {excerpt}
URL: {url}
Relevant hashtags: {hashtags_text}

Generate content for these platforms: {', '.join(platforms)}

For each platform, create:
1. Main text content optimized for that platform's character limits and audience expectations
2. Any platform-specific formatting (hashtags, mentions, etc.)

Format your response as a valid JSON object with each platform as a key and the content as the value.
For example:
{{
  "facebook": "Post content for Facebook...",
  "twitter": "Post content for Twitter...",
  ...
}}

Guidelines:
- Facebook: Engaging, conversational tone with 2-3 paragraphs and a question to encourage engagement
- Twitter: Concise, under 280 characters, with hashtags and a clear call to action
- LinkedIn: Professional tone, highlighting business value or insights, 1-2 paragraphs
- Instagram: Visual description with emotive language, liberal use of emojis and hashtags (in comment)

Ensure each post:
1. Grabs attention with an interesting hook or question
2. Includes the article URL (except for Instagram where it should mention "link in bio")
3. Has a clear call-to-action
4. Uses an appropriate tone for the platform
5. Includes relevant hashtags (more for Instagram/Twitter, fewer for LinkedIn/Facebook)
"""

        # Set up JSON response format
        response_format = {"type": "json_object"}
        
        # Get response from AI
        response = get_ai_response(
            prompt=prompt,
            model=Config.DEFAULT_SOCIAL_MODEL,
            temperature=0.7,
            response_format=response_format,
            system_prompt=system_prompt
        )
        
        # Process response
        if not response or not isinstance(response, dict):
            logger.error(f"Invalid response format: {response}")
            return generate_basic_social_content(title, excerpt, url, hashtags_text, platforms)
        
        # Validate and ensure all requested platforms are included
        for platform in platforms:
            if platform not in response:
                logger.warning(f"Missing content for {platform}, generating basic content")
                response[platform] = generate_basic_social_content_for_platform(
                    platform, title, excerpt, url, hashtags_text
                )
        
        return response
        
    except Exception as e:
        logger.error(f"Error creating social media content: {str(e)}")
        logger.error(traceback.format_exc())
        return generate_basic_social_content(title, excerpt, url, hashtags_text, platforms)

def generate_basic_social_content(
    title: str,
    excerpt: str,
    url: str,
    hashtags: str,
    platforms: List[str]
) -> Dict[str, str]:
    """
    Generate basic social media content when AI generation fails
    
    Args:
        title: Article title
        excerpt: Article excerpt
        url: Article URL
        hashtags: Formatted hashtags
        platforms: List of platforms
        
    Returns:
        Dictionary of platform-specific content
    """
    content = {}
    
    for platform in platforms:
        content[platform] = generate_basic_social_content_for_platform(
            platform, title, excerpt, url, hashtags
        )
    
    return content

def generate_basic_social_content_for_platform(
    platform: str,
    title: str,
    excerpt: str,
    url: str,
    hashtags: str
) -> str:
    """
    Generate basic social media content for a specific platform
    
    Args:
        platform: Social media platform
        title: Article title
        excerpt: Article excerpt
        url: Article URL
        hashtags: Formatted hashtags
        
    Returns:
        Platform-specific content
    """
    if platform == "facebook":
        return f"New blog post: {title}\n\n{excerpt}\n\nCheck it out here: {url}\n\n{hashtags}"
    
    elif platform == "twitter":
        # Truncate to fit Twitter's character limit
        short_title = title if len(title) < 70 else title[:67] + "..."
        return f"New post: {short_title}\n\nRead more: {url}\n\n{hashtags}"
    
    elif platform == "linkedin":
        return f"I've just published a new article: '{title}'\n\n{excerpt}\n\nRead the full article here: {url}\n\n{hashtags}"
    
    elif platform == "instagram":
        return f"New blog post: {title}\n\n{excerpt}\n\nCheck out the link in bio for the full article!\n\n{hashtags}"
    
    else:
        return f"Check out our new blog post: {title}\n\n{url}\n\n{hashtags}"

def post_to_facebook(
    account: SocialAccount,
    content: str,
    title: str,
    url: str,
    image_url: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Post content to Facebook
    
    Args:
        account: SocialAccount object with Facebook credentials
        content: Post content
        title: Article title
        url: Article URL
        image_url: Optional image URL
        
    Returns:
        Tuple of (success, post_id or error_message)
    """
    try:
        # This would use Facebook Graph API
        # For now, return success with mock response
        logger.info(f"Posted to Facebook: {title}")
        return True, f"facebook_post_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
    except Exception as e:
        logger.error(f"Error posting to Facebook: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e)

def post_to_twitter(
    account: SocialAccount,
    content: str,
    title: str,
    url: str,
    image_url: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Post content to Twitter
    
    Args:
        account: SocialAccount object with Twitter credentials
        content: Post content
        title: Article title
        url: Article URL
        image_url: Optional image URL
        
    Returns:
        Tuple of (success, post_id or error_message)
    """
    try:
        # This would use Twitter API v2
        # For now, return success with mock response
        logger.info(f"Posted to Twitter: {title}")
        return True, f"twitter_post_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
    except Exception as e:
        logger.error(f"Error posting to Twitter: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e)

def post_to_linkedin(
    account: SocialAccount,
    content: str,
    title: str,
    url: str,
    image_url: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Post content to LinkedIn
    
    Args:
        account: SocialAccount object with LinkedIn credentials
        content: Post content
        title: Article title
        url: Article URL
        image_url: Optional image URL
        
    Returns:
        Tuple of (success, post_id or error_message)
    """
    try:
        # This would use LinkedIn API
        # For now, return success with mock response
        logger.info(f"Posted to LinkedIn: {title}")
        return True, f"linkedin_post_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
    except Exception as e:
        logger.error(f"Error posting to LinkedIn: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e)

def post_to_instagram(
    account: SocialAccount,
    content: str,
    title: str,
    url: str,
    image_url: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Post content to Instagram
    
    Args:
        account: SocialAccount object with Instagram credentials
        content: Post content
        title: Article title
        url: Article URL
        image_url: Optional image URL (required for Instagram)
        
    Returns:
        Tuple of (success, post_id or error_message)
    """
    try:
        # Instagram requires an image
        if not image_url:
            return False, "Image URL is required for Instagram posts"
        
        # This would use Instagram Graph API
        # For now, return success with mock response
        logger.info(f"Posted to Instagram: {title}")
        return True, f"instagram_post_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
    except Exception as e:
        logger.error(f"Error posting to Instagram: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e)

def post_article_to_social_media(
    content_log_id: int,
    blog_id: int,
    title: str,
    excerpt: str,
    url: str,
    keywords: List[str],
    featured_image: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Post article to all active social media accounts for a blog
    
    Args:
        content_log_id: ID of the ContentLog entry
        blog_id: ID of the blog
        title: Article title
        excerpt: Article excerpt
        url: Article URL
        keywords: Article keywords
        featured_image: Featured image data
        
    Returns:
        Dictionary of platform-to-post_id mappings
    """
    try:
        # Import here to avoid circular imports
        from app import db
        
        # Get all active social media accounts for the blog
        social_accounts = SocialAccount.query.filter_by(
            blog_id=blog_id,
            active=True
        ).all()
        
        if not social_accounts:
            logger.warning(f"No active social media accounts found for blog {blog_id}")
            return {}
        
        # Get list of platforms
        platforms = [account.platform for account in social_accounts]
        
        # Generate social media content
        social_content = create_social_media_content(
            title=title,
            excerpt=excerpt,
            url=url,
            keywords=keywords,
            featured_image=featured_image,
            platforms=platforms
        )
        
        # Post to each platform
        post_results = {}
        
        for account in social_accounts:
            platform = account.platform
            content = social_content.get(platform, "")
            
            if not content:
                logger.warning(f"No content generated for {platform}")
                continue
            
            # Get image URL if available
            image_url = None
            if featured_image and 'url' in featured_image:
                image_url = featured_image['url']
            
            # Post to appropriate platform
            success = False
            post_id = None
            
            if platform == "facebook":
                success, post_id = post_to_facebook(account, content, title, url, image_url)
            elif platform == "twitter":
                success, post_id = post_to_twitter(account, content, title, url, image_url)
            elif platform == "linkedin":
                success, post_id = post_to_linkedin(account, content, title, url, image_url)
            elif platform == "instagram":
                success, post_id = post_to_instagram(account, content, title, url, image_url)
            else:
                logger.warning(f"Unsupported platform: {platform}")
                continue
            
            if success and post_id:
                post_results[platform] = post_id
        
        # Update ContentLog with social media posts
        if post_results:
            content_log = ContentLog.query.get(content_log_id)
            if content_log:
                content_log.set_social_posts(post_results)
                db.session.commit()
                logger.info(f"Updated ContentLog {content_log_id} with social media posts")
        
        return post_results
        
    except Exception as e:
        logger.error(f"Error posting article to social media: {str(e)}")
        logger.error(traceback.format_exc())
        return {}