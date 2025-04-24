"""
Social Media Publisher Utility Module
"""
import logging
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


def publish_post(social_account, title, excerpt, post_url, image_url=None):
    """
    Publish a post to a social media platform
    
    Args:
        social_account (SocialAccount): The social media account to publish to
        title (str): The title of the post
        excerpt (str): A short excerpt or description
        post_url (str): URL to the blog post
        image_url (str, optional): URL to featured image
        
    Returns:
        str: The ID of the created social media post
    """
    platform = social_account.platform.lower()
    
    if platform == 'facebook':
        return publish_to_facebook(social_account, title, excerpt, post_url, image_url)
    elif platform == 'twitter' or platform == 'x':
        return publish_to_twitter(social_account, title, excerpt, post_url, image_url)
    elif platform == 'linkedin':
        return publish_to_linkedin(social_account, title, excerpt, post_url, image_url)
    else:
        logger.warning(f"Unsupported platform: {platform}")
        return None


def publish_to_facebook(account, title, excerpt, post_url, image_url=None):
    """
    Publish a post to Facebook
    
    Args:
        account (SocialAccount): The Facebook account
        title (str): The title of the post
        excerpt (str): A short excerpt or description
        post_url (str): URL to the blog post
        image_url (str, optional): URL to featured image
        
    Returns:
        str: The ID of the created Facebook post
    """
    logger.info(f"Publishing to Facebook: {account.name}")
    
    # In a real implementation, this would use the Facebook Graph API
    # For simulation purposes, we'll just log and return a dummy post ID
    
    try:
        # Prepare message
        message = f"{title}\n\n{excerpt}\n\nRead more: {post_url}"
        
        # Log the action
        logger.info(f"Facebook post for account {account.name}: {message[:50]}...")
        
        # Return a dummy post ID
        return f"fb_post_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
    except Exception as e:
        logger.error(f"Error publishing to Facebook: {str(e)}")
        raise


def publish_to_twitter(account, title, excerpt, post_url, image_url=None):
    """
    Publish a post to Twitter
    
    Args:
        account (SocialAccount): The Twitter account
        title (str): The title of the post
        excerpt (str): A short excerpt or description
        post_url (str): URL to the blog post
        image_url (str, optional): URL to featured image
        
    Returns:
        str: The ID of the created tweet
    """
    logger.info(f"Publishing to Twitter: {account.name}")
    
    # In a real implementation, this would use the Twitter API
    # For simulation purposes, we'll just log and return a dummy tweet ID
    
    try:
        # Prepare tweet text (Twitter has a 280 character limit)
        # Create a short excerpt that fits within Twitter's character limit
        max_excerpt_length = 100
        short_excerpt = excerpt[:max_excerpt_length] + "..." if len(excerpt) > max_excerpt_length else excerpt
        
        tweet_text = f"{title}\n\n{short_excerpt}\n\n{post_url}"
        
        # Ensure tweet is within 280 characters
        if len(tweet_text) > 280:
            tweet_text = tweet_text[:276] + "..."
        
        # Log the action
        logger.info(f"Tweet for account {account.name}: {tweet_text[:50]}...")
        
        # Return a dummy tweet ID
        return f"tweet_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
    except Exception as e:
        logger.error(f"Error publishing to Twitter: {str(e)}")
        raise


def publish_to_linkedin(account, title, excerpt, post_url, image_url=None):
    """
    Publish a post to LinkedIn
    
    Args:
        account (SocialAccount): The LinkedIn account
        title (str): The title of the post
        excerpt (str): A short excerpt or description
        post_url (str): URL to the blog post
        image_url (str, optional): URL to featured image
        
    Returns:
        str: The ID of the created LinkedIn post
    """
    logger.info(f"Publishing to LinkedIn: {account.name}")
    
    # In a real implementation, this would use the LinkedIn API
    # For simulation purposes, we'll just log and return a dummy post ID
    
    try:
        # Prepare post content
        post_content = f"{title}\n\n{excerpt}\n\nRead more: {post_url}"
        
        # Log the action
        logger.info(f"LinkedIn post for account {account.name}: {post_content[:50]}...")
        
        # Return a dummy post ID
        return f"linkedin_post_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
    except Exception as e:
        logger.error(f"Error publishing to LinkedIn: {str(e)}")
        raise