"""
Content Generator Module

This module handles the generation of article content using AI.
"""
import logging
import os
import json
import re
import sys
from typing import Dict, List, Any, Optional

# Import our OpenRouter client
from utils.openrouter import openrouter
from config import Config

logger = logging.getLogger(__name__)

# Determine if we have a valid API key
openrouter_key = os.environ.get('OPENROUTER_API_KEY')
has_openrouter = openrouter_key is not None and len(openrouter_key) > 0

def generate_article(topic, keywords=None, style="informative", length="medium"):
    """
    Generate an article using AI
    
    Args:
        topic (str): The article topic or title
        keywords (list, optional): List of keywords to include
        style (str): Writing style (informative, conversational, professional, storytelling, persuasive)
        length (str): Content length (short, medium, long)
        
    Returns:
        dict: Generated content data including HTML, meta description, etc.
    """
    logger.info(f"Generating article content for topic: {topic}")
    
    # Convert length to exact word count
    word_count = {
        "short": 800,
        "medium": 1200,
        "long": 1600
    }.get(length, 1200)
    
    # Create the prompt for article generation with stronger emphasis on exact length
    user_prompt = f"""Write a comprehensive blog article about '{topic}' with EXACTLY {word_count} words.

Topic: {topic}
Style: {style}
Word count: EXACTLY {word_count} words (this is a non-negotiable requirement)
Keywords to include: {', '.join(keywords) if keywords else 'No specific keywords required'}

The article must be formatted with proper HTML structure including:
- An engaging headline (H1 tag)
- Introduction with a hook
- Well-organized sections with appropriate H2 and H3 subheadings
- Bullet points or numbered lists where appropriate
- A strong conclusion

CRITICAL REQUIREMENTS:
1. The article MUST contain EXACTLY {word_count} words - not more, not less. Count every word carefully.
2. After completion, verify the word count before providing the final result.
3. Do not include the word count in the article itself.
4. Be comprehensive and add valuable content - avoid fluff or filler text.
5. Include real examples, case studies, statistics, or research data as needed.
6. The article should be factually accurate, well-researched, and provide real value to readers.

After completing the article with EXACTLY {word_count} words, please also include:
- Meta description (under 160 characters)
- Brief excerpt for social sharing (2-3 sentences)
- 3-5 tags for the article (comma-separated)"""

    # System prompt to guide the AI's behavior
    system_prompt = """You are an expert content writer specializing in creating high-quality blog articles.
Your task is to write a well-structured, engaging, and informative article following the exact specifications provided.
Focus on accuracy, readability, and meeting the exact word count requirements."""

    # Check if we have access to OpenRouter
    if has_openrouter:
        try:
            # Get default content model from config
            model = Config.DEFAULT_CONTENT_MODEL or "anthropic/claude-3-sonnet-20240229"
            
            # Send request to OpenRouter
            logger.info(f"Generating content using model: {model}")
            
            # Use our direct OpenRouter client
            content = openrouter.generate_completion(
                prompt=user_prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=4000
            )
            
            if not content:
                logger.error("Failed to get content from OpenRouter")
                return _get_mock_content(topic, keywords, style, length)
            
            # Extract content sections
            html_content = _extract_html_content(content)
            meta_description = _extract_meta_description(content)
            excerpt = _extract_excerpt(content)
            
            # Generate tags
            tags = _generate_tags_from_content(topic, keywords, content)
            
            return {
                "content": html_content,
                "meta_description": meta_description,
                "excerpt": excerpt,
                "tags": tags,
                "featured_image_url": ""  # In a real implementation, this would be generated or fetched
            }
            
        except Exception as e:
            logger.error(f"Error generating content with AI: {str(e)}")
            return _get_mock_content(topic, keywords, style, length)
    else:
        # No API key, return mock content
        logger.warning("No OpenRouter API key available")
        return _get_mock_content(topic, keywords, style, length)


def _extract_html_content(content):
    """
    Extract HTML content from the AI response
    
    Args:
        content (str): The AI-generated content
        
    Returns:
        str: Clean HTML content
    """
    # Look for HTML content between opening and closing tags
    html_start = content.find("<h1")
    if html_start == -1:
        html_start = content.find("<H1")
    
    html_end = content.rfind("</p>")
    if html_end == -1:
        html_end = content.rfind("</P>")
    
    if html_start != -1 and html_end != -1:
        return content[html_start:html_end+4]
    
    # If no clear HTML, return the whole content
    return content


def _extract_meta_description(content):
    """
    Extract meta description from the AI response
    
    Args:
        content (str): The AI-generated content
        
    Returns:
        str: Meta description
    """
    meta_desc_patterns = [
        r"(?i)Meta\s*Description:\s*\"?([^\"]+)\"?",
        r"(?i)Meta\s*Description:\s*(.+?)(?:\n|$)",
        r"(?i)<meta\s+name=\"description\"\s+content=\"([^\"]+)\"",
    ]
    
    for pattern in meta_desc_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
    
    # If no meta description found, create one from the first paragraph
    paragraphs = re.findall(r"<p>(.*?)</p>", content, re.DOTALL)
    if paragraphs:
        # Clean the first paragraph of any HTML and limit to ~155 chars
        first_para = re.sub(r"<.*?>", "", paragraphs[0])
        if len(first_para) > 155:
            return first_para[:152] + "..."
        return first_para
        
    return ""


def _extract_excerpt(content):
    """
    Extract excerpt from the AI response
    
    Args:
        content (str): The AI-generated content
        
    Returns:
        str: Excerpt
    """
    excerpt_patterns = [
        r"(?i)Excerpt:\s*\"?([^\"]+)\"?",
        r"(?i)Excerpt:\s*(.+?)(?:\n|$)",
    ]
    
    for pattern in excerpt_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip()
    
    # If no excerpt found, use the meta description
    meta_desc = _extract_meta_description(content)
    if meta_desc:
        return meta_desc
        
    return ""


def _generate_tags_from_content(topic, keywords, content):
    """
    Generate tags from the content
    
    Args:
        topic (str): The article topic
        keywords (list): List of keywords
        content (str): The article content
        
    Returns:
        list: Generated tags
    """
    # Start with keywords if available
    tags = list(keywords) if keywords else []
    
    # Add the main topic as a tag if not already present
    topic_words = topic.lower().split()
    for word in topic_words:
        if len(word) > 3 and word not in [t.lower() for t in tags]:
            tags.append(word.capitalize())
    
    # Limit to 5 tags maximum
    return tags[:5]


def _get_mock_content(topic, keywords, style, length):
    """
    Generate mock content when API is not available
    
    Args:
        topic (str): The article topic
        keywords (list): List of keywords
        style (str): Writing style
        length (str): Content length
        
    Returns:
        dict: Mock content data
    """
    logger.warning("Using mock content generator")
    
    title = f"The Complete Guide to {topic}"
    
    html_content = f"""
    <h1>{title}</h1>
    <p>This is a sample article about {topic}. In a real implementation, this would be generated using AI.</p>
    <h2>Key Points About {topic}</h2>
    <p>Here are some important aspects to consider when discussing {topic}:</p>
    <ul>
        <li>First key point about {topic}</li>
        <li>Second key point about {topic}</li>
        <li>Third key point about {topic}</li>
    </ul>
    <h2>Best Practices for {topic}</h2>
    <p>When implementing {topic}, consider these best practices:</p>
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam in dui mauris.</p>
    <h3>Advanced Strategies</h3>
    <p>For those looking to take their {topic} to the next level:</p>
    <p>Vestibulum pellentesque felis eu massa. Quisque ullamcorper placerat ipsum.</p>
    <h2>Conclusion</h2>
    <p>In conclusion, {topic} is an important subject that requires careful consideration.</p>
    """
    
    meta_description = f"Learn everything you need to know about {topic} in this comprehensive guide. We cover key concepts, best practices, and advanced strategies."
    
    excerpt = f"This comprehensive guide explores {topic} in detail, providing you with essential knowledge and practical tips."
    
    tags = [topic] + (keywords if keywords else [])
    
    return {
        "content": html_content,
        "meta_description": meta_description,
        "excerpt": excerpt,
        "tags": tags[:5],
        "featured_image_url": ""
    }