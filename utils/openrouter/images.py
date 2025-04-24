import logging
import json
import base64
import time
from typing import List, Dict, Any, Optional
from utils.openrouter import openrouter
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

def generate_image_prompts(
    title: str,
    content_snippet: str,
    keywords: List[str],
    style: str = "realistic",
    count: int = 3
) -> List[str]:
    """
    Generate high-quality image generation prompts for an article
    
    Args:
        title: Article title
        content_snippet: Brief excerpt of content for context
        keywords: Key topics/themes of the article
        style: Visual style for images (realistic, minimalist, etc.)
        count: Number of prompts to generate
        
    Returns:
        List of detailed image generation prompts
    """
    keywords_text = ", ".join(keywords)
    
    prompt = f"""
    Generate {count} detailed image prompts for article illustrations based on the following information:
    
    Article Title: {title}
    Content Excerpt: {content_snippet}
    Key Topics: {keywords_text}
    Visual Style: {style}
    
    For each prompt:
    1. Create a detailed description of the image scene
    2. Include specific visual elements, subjects, lighting, and perspective 
    3. Mention color palette and mood
    4. Optimize for high-quality image generation with AI
    
    Format your response as a JSON array of strings, with each string being a complete image prompt:
    [
        "Detailed image prompt 1",
        "Detailed image prompt 2",
        "Detailed image prompt 3"
    ]
    """
    
    # Get model for image prompt generation
    model = openrouter.get_topic_model()  # Use topic model for more creative prompts
    
    try:
        # Send to OpenRouter for prompt generation
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are an expert image prompt engineer who specializes in creating detailed, effective prompts for AI image generation. Your prompts should be specific, descriptive, and designed to produce high-quality, relevant images for blog articles.",
            temperature=0.8  # Higher temperature for creative image prompts
        )
        
        if not response or not isinstance(response, list):
            logger.error("Failed to generate image prompts")
            return [f"A professional {style} image related to {keywords_text}" for _ in range(count)]
        
        return response[:count]  # Ensure we only return the requested number
    except Exception as e:
        logger.error(f"Error generating image prompts: {str(e)}")
        return [f"A professional {style} image related to {keywords_text}" for _ in range(count)]

def suggest_image_locations(content: str) -> List[Dict[str, Any]]:
    """
    Analyze article content and suggest optimal image placements
    
    Args:
        content: HTML content of the article
        
    Returns:
        List of dictionaries with image placement suggestions
    """
    # Truncate content for prompt if too long
    content_sample = content[:5000] + "..." if len(content) > 5000 else content
    
    prompt = f"""
    Analyze the following article content and suggest optimal locations for image placements:
    
    {content_sample}
    
    For each suggested image:
    1. Identify the appropriate location (after which paragraph or heading)
    2. Describe what the image should contain to support the surrounding content
    3. Suggest an appropriate caption
    4. Explain why an image would be effective at this location
    
    Format your response as a JSON array with the following structure:
    [
        {{
            "location": "After the first paragraph",
            "description": "Description of the image content",
            "caption": "Suggested image caption",
            "reasoning": "Why an image works well here"
        }},
        ...
    ]
    
    Suggest between 3-5 image locations, focusing on the most impactful positions.
    """
    
    # Get model for content analysis
    model = openrouter.get_content_model()
    
    try:
        # Send to OpenRouter for analysis
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are a visual content strategist who specializes in optimizing article layouts. Identify the most strategic locations for images within an article to enhance reader engagement, support key points, and create visual breaks in the content.",
            temperature=0.4  # Lower temperature for more practical analysis
        )
        
        if not response or not isinstance(response, list):
            logger.error("Failed to suggest image locations")
            return []
        
        return response
    except Exception as e:
        logger.error(f"Error suggesting image locations: {str(e)}")
        return []

def generate_image_alt_text(
    image_description: str,
    article_context: Optional[str] = None
) -> str:
    """
    Generate SEO-optimized alt text for article images
    
    Args:
        image_description: Description of the image content
        article_context: Optional context from the article
        
    Returns:
        SEO-optimized alt text
    """
    context = f"Article Context: {article_context}\n" if article_context else ""
    
    prompt = f"""
    Generate an SEO-optimized alt text for an image with the following description:
    
    {context}
    Image Description: {image_description}
    
    The alt text should:
    1. Be concise (under 125 characters)
    2. Be descriptive of the image content
    3. Include relevant keywords naturally
    4. Provide context relative to the article
    5. Be useful for both screen readers and SEO
    
    Provide just the alt text itself, without quotes or explanations.
    """
    
    # Get model for alt text generation
    model = openrouter.get_topic_model()  # Use lighter model for simple alt text
    
    try:
        # Send to OpenRouter for alt text generation
        response = openrouter.generate_completion(
            prompt=prompt,
            model=model,
            system_prompt="You are an accessibility and SEO specialist who creates perfect image alt text. Create concise, descriptive alt text that serves both screen reader users and search engines.",
            temperature=0.3  # Lower temperature for more precise alt text
        )
        
        if not response:
            logger.error("Failed to generate image alt text")
            return image_description[:125]  # Use truncated description as fallback
        
        # Trim any quotes or extra whitespace
        alt_text = response.strip().strip('"\'')
        
        # Ensure alt text isn't too long
        if len(alt_text) > 125:
            alt_text = alt_text[:122] + "..."
        
        return alt_text
    except Exception as e:
        logger.error(f"Error generating image alt text: {str(e)}")
        return image_description[:125]  # Use truncated description as fallback

def enhance_image_metadata(
    image_url: str,
    article_title: str,
    article_keywords: List[str]
) -> Dict[str, Any]:
    """
    Generate enhanced metadata for an image to improve SEO
    
    Args:
        image_url: URL of the image
        article_title: Title of the article
        article_keywords: Keywords for the article
        
    Returns:
        Dictionary with enhanced image metadata
    """
    keywords_text = ", ".join(article_keywords)
    
    prompt = f"""
    Generate enhanced SEO metadata for an image used in the following article:
    
    Article Title: {article_title}
    Keywords: {keywords_text}
    Image URL: {image_url}
    
    Create comprehensive metadata including:
    1. An SEO-optimized filename (without spaces, using hyphens)
    2. A descriptive alt text (under 125 characters)
    3. A longer image description for the caption
    4. Relevant keywords for the image
    5. Suggested image title attribute text
    
    Format your response as a JSON object with the following structure:
    {{
        "filename": "seo-optimized-filename.jpg",
        "alt_text": "Descriptive alt text for accessibility and SEO",
        "caption": "Longer caption text that adds context and includes keywords naturally",
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "title": "Text for the title attribute"
    }}
    """
    
    # Get model for metadata generation
    model = openrouter.get_topic_model()
    
    try:
        # Send to OpenRouter for metadata generation
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are an image SEO specialist who optimizes images for both search engines and user experience. Create comprehensive, effective metadata that improves discoverability and accessibility.",
            temperature=0.4
        )
        
        if not response:
            logger.error("Failed to enhance image metadata")
            
            # Create basic fallback metadata
            image_name = article_title.lower().replace(" ", "-")[:50]
            alt_text = f"Image related to {article_title}"
            
            return {
                "filename": f"{image_name}.jpg",
                "alt_text": alt_text,
                "caption": article_title,
                "keywords": article_keywords[:5],
                "title": article_title
            }
        
        return response
    except Exception as e:
        logger.error(f"Error enhancing image metadata: {str(e)}")
        
        # Create basic fallback metadata
        image_name = article_title.lower().replace(" ", "-")[:50]
        alt_text = f"Image related to {article_title}"
        
        return {
            "filename": f"{image_name}.jpg",
            "alt_text": alt_text,
            "caption": article_title,
            "keywords": article_keywords[:5],
            "title": article_title
        }