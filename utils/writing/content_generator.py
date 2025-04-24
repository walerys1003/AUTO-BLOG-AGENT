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

# Import libraries for AI content generation
import anthropic
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# Initialize the AI client
anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
openrouter_key = os.environ.get('OPENROUTER_API_KEY')

# Try to use OpenRouter API key first, then fall back to Anthropic direct
if openrouter_key:
    # When using OpenRouter, we need to configure anthropic client with OpenRouter endpoint
    client = Anthropic(
        api_key=openrouter_key,
        base_url="https://openrouter.ai/api/v1",
    )
elif anthropic_key:
    # Direct connection to Anthropic
    client = Anthropic(
        api_key=anthropic_key,
    )
else:
    logger.warning("No API keys found for content generation. Using mock responses.")
    client = None

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
    
    # Convert length to approximate word count
    word_count = {
        "short": 600,
        "medium": 1200,
        "long": 1800
    }.get(length, 1200)
    
    # Create the prompt
    system_prompt = f"""You are an expert content writer specializing in creating high-quality blog articles.
Your task is to write a well-structured, engaging, and informative article on the provided topic.

Article specifications:
- Topic: {topic}
- Style: {style}
- Target length: Approximately {word_count} words
- Keywords to include: {', '.join(keywords) if keywords else 'No specific keywords required'}

Please format the article with proper HTML structure including:
1. An engaging headline (H1 tag)
2. Introduction with a hook
3. Well-organized sections with appropriate H2 and H3 subheadings
4. Bullet points or numbered lists where appropriate
5. A strong conclusion
6. Include a meta description and excerpt for SEO purposes

The article should be factually accurate, well-researched, and provide real value to readers.
Be creative but professional, and make the content readable and engaging for web audiences."""

    user_prompt = f"Please write a complete blog article about '{topic}' following the specifications I've provided."

    # If we have a client, use it to generate content
    if client:
        try:
            # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000
            )
            
            content = response.content[0].text
            
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