import logging
import json
import time
from typing import List, Dict, Any, Optional
from utils.openrouter import openrouter
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

def generate_social_media_content(
    title: str,
    excerpt: str,
    url: str,
    platforms: List[str],
    keywords: Optional[List[str]] = None,
    image_description: Optional[str] = None
) -> Dict[str, Dict[str, str]]:
    """
    Generate platform-specific social media posts for an article
    
    Args:
        title: Article title
        excerpt: Article excerpt or summary
        url: URL to the article
        platforms: List of platforms (facebook, twitter, linkedin, instagram)
        keywords: Optional target keywords/hashtags
        image_description: Optional description of featured image
        
    Returns:
        Dictionary with platform-specific content
    """
    if not platforms:
        logger.warning("No platforms specified for social media content")
        return {}
    
    platforms_str = ", ".join(platforms)
    keywords_str = ", ".join(keywords) if keywords else ""
    
    prompt = f"""
    Generate engaging social media posts for the following article:
    
    Title: {title}
    Excerpt: {excerpt}
    URL: {url}
    Keywords/hashtags: {keywords_str}
    Featured image description: {image_description or "Not provided"}
    
    Create custom content for each of these platforms: {platforms_str}
    
    For each platform, follow these best practices:
    - Facebook: Conversational, 1-2 paragraphs, 1-2 hashtags, engaging question
    - Twitter: Concise, under 280 chars, 2-3 relevant hashtags, clear CTA
    - LinkedIn: Professional tone, business insights, 2-3 paragraphs, industry hashtags
    - Instagram: Visual focus, emoji use, 5-10 relevant hashtags, conversational
    
    Format your response as a JSON object with the following structure:
    {{
        "facebook": {{
            "content": "Complete post content for Facebook",
            "hashtags": ["hashtag1", "hashtag2"]
        }},
        "twitter": {{
            "content": "Complete post content for Twitter",
            "hashtags": ["hashtag1", "hashtag2", "hashtag3"]
        }},
        "linkedin": {{
            "content": "Complete post content for LinkedIn",
            "hashtags": ["hashtag1", "hashtag2"]
        }},
        "instagram": {{
            "content": "Complete post content for Instagram",
            "hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4"]
        }}
    }}
    
    Only include the platforms requested in the original list.
    """
    
    # Get model for social media content
    model = openrouter.get_social_model()
    
    try:
        # Send to OpenRouter for content generation
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are a social media marketing expert who specializes in creating platform-specific content that drives engagement and clicks. Craft compelling, native-feeling posts that follow each platform's best practices and unique culture.",
            temperature=0.8  # Higher temperature for creative social content
        )
        
        if not response:
            logger.error("Failed to generate social media content")
            return {platform: {"content": f"Check out our latest post: {title} {url}", "hashtags": []} for platform in platforms}
        
        # Validate that we have content for all requested platforms
        for platform in platforms:
            if platform not in response:
                logger.warning(f"Missing content for platform: {platform}")
                response[platform] = {
                    "content": f"Check out our latest post: {title} {url}",
                    "hashtags": []
                }
        
        return response
    except Exception as e:
        logger.error(f"Error generating social media content: {str(e)}")
        return {platform: {"content": f"Check out our latest post: {title} {url}", "hashtags": []} for platform in platforms}

def generate_hashtag_recommendations(
    title: str,
    keywords: List[str],
    category: str,
    platform: str = "all"
) -> Dict[str, List[str]]:
    """
    Generate recommended hashtags for social media posts
    
    Args:
        title: Article title
        keywords: Article keywords
        category: Article category
        platform: Specific platform or "all"
        
    Returns:
        Dictionary with platform-specific hashtag recommendations
    """
    keywords_str = ", ".join(keywords)
    
    prompt = f"""
    Generate recommended hashtags for social media posts about the following article:
    
    Title: {title}
    Keywords: {keywords_str}
    Category: {category}
    
    Provide hashtag recommendations for the following platforms:
    - Facebook: 2-3 relevant hashtags, more general
    - Twitter: 3-4 trending, relevant hashtags
    - LinkedIn: 3-5 industry-focused, professional hashtags
    - Instagram: 10-15 mixed popularity hashtags, including niche and general ones
    
    For each platform, include:
    1. A mix of popular and niche hashtags
    2. Category-specific hashtags
    3. Trending hashtags when relevant
    
    Format your response as a JSON object with the following structure:
    {{
        "facebook": ["hashtag1", "hashtag2", "hashtag3"],
        "twitter": ["hashtag1", "hashtag2", "hashtag3", "hashtag4"],
        "linkedin": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"],
        "instagram": ["hashtag1", "hashtag2", "hashtag3", ...]
    }}
    """
    
    # Get model for hashtag recommendations
    model = openrouter.get_social_model()
    
    try:
        # Send to OpenRouter for hashtag recommendations
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are a social media specialist who excels at identifying optimal hashtags for different platforms. Recommend hashtags that will maximize reach and engagement while remaining relevant to the content.",
            temperature=0.6
        )
        
        if not response:
            logger.error("Failed to generate hashtag recommendations")
            return {
                "facebook": keywords[:2],
                "twitter": keywords[:3],
                "linkedin": keywords[:3],
                "instagram": keywords
            }
        
        # If requesting for a specific platform, return only that platform's hashtags
        if platform != "all" and platform in response:
            return {platform: response[platform]}
        
        return response
    except Exception as e:
        logger.error(f"Error generating hashtag recommendations: {str(e)}")
        return {
            "facebook": keywords[:2],
            "twitter": keywords[:3],
            "linkedin": keywords[:3],
            "instagram": keywords
        }

def analyze_social_media_engagement(
    platform: str, 
    post_content: str,
    target_audience: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze potential engagement for social media post content
    
    Args:
        platform: Social media platform
        post_content: The content of the post
        target_audience: Optional description of target audience
        
    Returns:
        Dictionary with engagement analysis
    """
    audience_context = f"Target audience: {target_audience}\n" if target_audience else ""
    
    prompt = f"""
    Analyze the following social media post for {platform} and predict potential engagement:
    
    {audience_context}
    Post content:
    {post_content}
    
    Provide detailed analysis on:
    1. Predicted engagement level (reactions, comments, shares)
    2. Content strengths and weaknesses
    3. Emotional triggers present
    4. Call-to-action effectiveness
    5. Optimization recommendations
    
    Format your response as a JSON object with the following structure:
    {{
        "engagement_prediction": "high|medium|low",
        "strengths": ["strength1", "strength2", ...],
        "weaknesses": ["weakness1", "weakness2", ...],
        "emotional_triggers": ["trigger1", "trigger2", ...],
        "cta_effectiveness": "strong|moderate|weak",
        "recommendations": ["recommendation1", "recommendation2", ...]
    }}
    """
    
    # Get model for engagement analysis
    model = openrouter.get_social_model()
    
    try:
        # Send to OpenRouter for analysis
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are a social media analytics expert who specializes in predicting engagement patterns and optimizing content for maximum impact. Provide data-driven insights on how content will perform and how it can be improved.",
            temperature=0.4  # Lower temperature for more analytical responses
        )
        
        if not response:
            logger.error("Failed to analyze social media engagement")
            return {
                "success": False,
                "message": "Failed to analyze engagement",
                "data": {}
            }
        
        return {
            "success": True,
            "message": "Engagement analysis completed",
            "data": response
        }
    except Exception as e:
        logger.error(f"Error analyzing social media engagement: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": {}
        }