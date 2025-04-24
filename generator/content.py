import logging
import json
from typing import Dict, Any, List, Optional
import traceback
import random
from datetime import datetime
from config import Config
from utils.helpers import get_ai_response, clean_html

# Setup logging
logger = logging.getLogger(__name__)

def generate_article_content(
    title: str, 
    keywords: List[str], 
    category: str, 
    blog_name: str,
    min_length: int = None,
    max_length: int = None
) -> Dict[str, Any]:
    """
    Generate a complete blog article with SEO optimization
    
    Args:
        title: Article title
        keywords: List of target keywords
        category: Article category
        blog_name: Name of the blog
        min_length: Minimum article length in words
        max_length: Maximum article length in words
        
    Returns:
        Dictionary with article content, meta description, excerpt, and tags
    """
    # Use configured length limits or defaults
    min_length = min_length or Config.ARTICLE_MIN_LENGTH
    max_length = max_length or Config.ARTICLE_MAX_LENGTH
    
    try:
        # Construct a detailed prompt for article generation
        prompt = f"""
        Create a comprehensive, engaging, and SEO-optimized blog article for a blog named "{blog_name}" with the following specifications:
        
        TITLE: {title}
        CATEGORY: {category}
        TARGET KEYWORDS: {', '.join(keywords)}
        LENGTH: Between {min_length} and {max_length} words
        
        Please structure the article with:
        1. An engaging introduction that hooks the reader
        2. Clear and well-organized H2 and H3 headings (using ## and ### format)
        3. Informative and valuable content with practical advice
        4. A conclusion that summarizes key points
        5. Naturally incorporated keywords throughout the text (not forced)
        
        Also, I need:
        - A compelling meta description (150-160 characters)
        - A brief excerpt/intro (80-120 words)
        - 10-15 relevant tags for the article
        
        Format the response as valid JSON with the following fields:
        - content: The full article content with heading markup
        - html_content: The article with proper HTML tags (p, h2, h3, ul, li, etc.)
        - meta_description: SEO meta description
        - excerpt: Article excerpt/intro
        - tags: Array of tags

        Today's date is {datetime.now().strftime('%Y-%m-%d')}.
        """
        
        # Request article generation from AI
        response = get_ai_response(
            prompt=prompt,
            model=Config.DEFAULT_CONTENT_MODEL,
            response_format={"type": "json_object"}
        )
        
        if not response or not isinstance(response, dict):
            logger.error("Invalid response format from AI")
            return generate_fallback_article(title, keywords, category)
        
        # Ensure HTML content is properly formatted and clean
        if "html_content" in response:
            response["html_content"] = clean_html(response["html_content"])
        elif "content" in response:
            # Convert markdown to HTML if html_content not provided
            from markdown import markdown
            html_content = markdown(response["content"])
            response["html_content"] = clean_html(html_content)
        
        # Validate and add missing fields
        required_fields = ["content", "html_content", "meta_description", "excerpt", "tags"]
        for field in required_fields:
            if field not in response:
                if field == "tags" and keywords:
                    response["tags"] = keywords
                elif field == "excerpt" and "content" in response:
                    # Create excerpt from content if missing
                    words = response["content"].split()[:50]
                    response["excerpt"] = " ".join(words) + "..."
                elif field == "meta_description" and "excerpt" in response:
                    # Use excerpt as meta description if missing
                    response["meta_description"] = response["excerpt"][:160]
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating article content: {str(e)}")
        logger.error(traceback.format_exc())
        return generate_fallback_article(title, keywords, category)

def generate_fallback_article(title: str, keywords: List[str], category: str) -> Dict[str, Any]:
    """
    Generate a basic fallback article when AI generation fails
    
    Args:
        title: Article title
        keywords: List of target keywords
        category: Article category
        
    Returns:
        Basic article with required fields
    """
    logger.info("Generating fallback article")
    
    # Create a basic article structure
    intro = f"In this article, we'll explore {title}. This is an important topic in the {category} space that deserves attention."
    
    sections = [
        f"## Understanding {keywords[0] if keywords else 'the Basics'}",
        f"Let's begin by understanding what {keywords[0] if keywords else 'this topic'} is all about. It's essential to grasp the fundamentals before diving deeper.",
        
        f"## Key Benefits and Considerations",
        f"There are several important aspects to consider when it comes to {title}. Let's explore the most significant ones.",
        
        "### Important Points to Remember",
        "- Always research thoroughly before making decisions",
        "- Consider consulting with experts in the field",
        "- Stay updated with the latest developments",
        "- Practice regularly to improve your skills",
        
        f"## Best Practices for {keywords[1] if len(keywords) > 1 else 'Success'}",
        f"Following best practices will help you achieve better results with {keywords[1] if len(keywords) > 1 else 'this topic'}.",
        
        "## Conclusion",
        f"In conclusion, {title} is a fascinating subject that continues to evolve. By staying informed and applying the principles discussed in this article, you'll be better equipped to navigate this area successfully."
    ]
    
    # Combine sections into full content
    content = intro + "\n\n" + "\n\n".join(sections)
    
    # Convert markdown to HTML
    from markdown import markdown
    html_content = markdown(content)
    
    # Create meta description
    meta_description = f"Learn everything you need to know about {title}. This comprehensive guide covers key concepts, best practices, and expert tips for {keywords[0] if keywords else 'success'}."
    
    return {
        "content": content,
        "html_content": html_content,
        "meta_description": meta_description[:160],
        "excerpt": intro,
        "tags": keywords if keywords else [category, "guide", "tutorial", "tips", "advice"]
    }

def generate_article_title_suggestions(category: str, keywords: List[str], count: int = 3) -> List[str]:
    """
    Generate engaging article title suggestions based on category and keywords
    
    Args:
        category: Article category
        keywords: Target keywords to include
        count: Number of titles to generate
        
    Returns:
        List of suggested titles
    """
    try:
        key_phrase = keywords[0] if keywords else category
        
        prompt = f"""
        Generate {count} engaging, click-worthy, and SEO-optimized blog titles for an article about {key_phrase}.
        
        Category: {category}
        Keywords to incorporate: {', '.join(keywords[:5])}
        
        The titles should:
        - Be 50-65 characters long
        - Naturally incorporate a primary keyword
        - Be compelling and encourage clicks
        - Not use clickbait tactics
        
        Format your response as a JSON array of strings containing just the titles.
        """
        
        response = get_ai_response(
            prompt=prompt,
            model=Config.DEFAULT_TOPIC_MODEL,
            response_format={"type": "json_object"}
        )
        
        if response and isinstance(response, dict) and "titles" in response:
            return response["titles"]
        elif response and isinstance(response, list):
            return response
        else:
            return generate_basic_titles(category, keywords, count)
            
    except Exception as e:
        logger.error(f"Error generating title suggestions: {str(e)}")
        return generate_basic_titles(category, keywords, count)

def generate_basic_titles(category: str, keywords: List[str], count: int) -> List[str]:
    """
    Generate basic article titles when AI generation fails
    
    Args:
        category: Article category
        keywords: Target keywords
        count: Number of titles to generate
        
    Returns:
        List of basic titles
    """
    key_phrase = keywords[0] if keywords else category
    
    templates = [
        f"The Ultimate Guide to {key_phrase}",
        f"10 Essential {key_phrase} Tips You Need to Know",
        f"How to Master {key_phrase}: A Step-by-Step Guide",
        f"Why {key_phrase} Matters: Expert Insights",
        f"The Complete Beginner's Guide to {key_phrase}",
        f"The Future of {key_phrase}: Trends and Predictions",
        f"{key_phrase} 101: Everything You Need to Know",
        f"7 Proven Strategies for {key_phrase} Success",
        f"Understanding {key_phrase}: A Comprehensive Overview",
        f"The Pros and Cons of {key_phrase}: An Honest Analysis"
    ]
    
    # Return requested number of titles
    return random.sample(templates, min(count, len(templates)))
