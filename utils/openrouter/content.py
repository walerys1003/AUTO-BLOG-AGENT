import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from utils.openrouter import openrouter
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

def generate_article_content(
    title: str,
    keywords: List[str],
    category: str,
    blog_name: str,
    tone: str = "professional",
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate a complete blog article using AI
    
    Args:
        title: Article title
        keywords: Target keywords to include
        category: Article category
        blog_name: Name of the blog
        tone: Content tone (professional, casual, educational, etc.)
        min_length: Minimum word count
        max_length: Maximum word count
        
    Returns:
        Dictionary with article content and metadata
    """
    # Use config defaults if not specified
    if min_length is None:
        min_length = Config.ARTICLE_MIN_LENGTH
    if max_length is None:
        max_length = Config.ARTICLE_MAX_LENGTH
    
    keywords_text = ", ".join(keywords)
    
    prompt = f"""
    Write a comprehensive blog article for {blog_name} with the following specifications:
    
    Title: {title}
    Category: {category}
    Keywords to include: {keywords_text}
    Tone: {tone}
    Length: Between {min_length} and {max_length} words
    
    Please include the following elements:
    1. An engaging introduction that hooks the reader
    2. Well-structured sections with proper H2 and H3 headings
    3. Practical examples, data points, or case studies where relevant
    4. A conclusion with clear takeaways or next steps
    5. Natural inclusion of the target keywords throughout the text
    
    Also provide:
    - A meta description (under 160 characters)
    - A brief excerpt for social sharing (2-3 sentences)
    - 5-8 tags for the article
    
    Format your response as a JSON object with the following structure:
    {{
        "content": "The complete HTML content of the article",
        "meta_description": "SEO meta description",
        "excerpt": "Brief excerpt for social sharing",
        "tags": ["tag1", "tag2", "tag3"]
    }}
    """
    
    # Get model for content generation
    model = openrouter.get_content_model()
    
    try:
        # Use a higher token limit for content generation
        max_tokens = 4000  # Adjust based on the model's capabilities
        
        # Send to OpenRouter for content generation
        start_time = time.time()
        logger.info(f"Generating article content for '{title}' using model {model}")
        
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are an expert content writer who specializes in creating SEO-optimized blog articles that are engaging, informative, and valuable to readers. Write in a clear, conversational style that naturally incorporates target keywords. Structure content with proper HTML tags for headings, paragraphs, lists, and other elements.",
            temperature=0.7
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        if not response:
            logger.error("Failed to generate article content")
            return {}
        
        logger.info(f"Generated article in {generation_time:.2f} seconds")
        
        # Validate required fields
        required_fields = ["content", "meta_description", "excerpt", "tags"]
        for field in required_fields:
            if field not in response:
                logger.warning(f"Missing required field '{field}' in generated content")
                # Add empty value for missing field
                response[field] = "" if field != "tags" else []
        
        return response
    except Exception as e:
        logger.error(f"Error generating article content: {str(e)}")
        return {}

def generate_content_variations(
    original_content: str,
    count: int = 3,
    variation_type: str = "title"
) -> List[str]:
    """
    Generate variations of content (titles, excerpts, etc.)
    
    Args:
        original_content: The original content to vary
        count: Number of variations to generate
        variation_type: Type of content to vary (title, excerpt, meta)
        
    Returns:
        List of content variations
    """
    type_descriptions = {
        "title": "headline variations that maintain the same meaning but use different wording",
        "excerpt": "excerpt variations that highlight different aspects of the content",
        "meta": "meta description variations optimized for different search intents"
    }
    
    description = type_descriptions.get(variation_type, "variations of the content")
    
    prompt = f"""
    Generate {count} different {description} for the following content:
    
    {original_content}
    
    Format your response as a JSON array of strings:
    [
        "Variation 1",
        "Variation 2",
        "Variation 3"
    ]
    """
    
    # Get appropriate model based on variation type
    model = openrouter.get_topic_model()  # Use lighter model for simple variations
    
    try:
        # Send to OpenRouter for variations
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt=f"You are a content optimization specialist who excels at creating compelling {variation_type} variations. Maintain the original meaning and intent while providing unique phrasing and structure.",
            temperature=0.8  # Higher temperature for more creative variations
        )
        
        if not response or not isinstance(response, list):
            logger.error("Failed to generate content variations")
            return []
        
        return response[:count]  # Ensure we only return the requested number
    except Exception as e:
        logger.error(f"Error generating content variations: {str(e)}")
        return []

def optimize_article_readability(content: str) -> Tuple[str, Dict[str, Any]]:
    """
    Optimize article readability and structure
    
    Args:
        content: Article HTML content
        
    Returns:
        Tuple of (optimized content, analysis results)
    """
    # Truncate content for prompt if too long
    content_sample = content[:5000] + "..." if len(content) > 5000 else content
    
    prompt = f"""
    Analyze and optimize the following article content for readability, engagement, and structure:
    
    {content_sample}
    
    Please:
    1. Improve sentence and paragraph structure for better readability
    2. Enhance transitions between sections
    3. Optimize heading hierarchy and formatting
    4. Add bullet points or numbered lists where appropriate
    5. Suggest pull quotes or callout sections
    
    Provide both the optimized content and an analysis of the changes made.
    
    Format your response as a JSON object with the following structure:
    {{
        "optimized_content": "The complete optimized HTML content",
        "analysis": {{
            "readability_score": "improved score (e.g., 75/100)",
            "changes_made": [
                "description of change 1",
                "description of change 2"
            ],
            "recommendations": [
                "additional recommendation 1",
                "additional recommendation 2"
            ]
        }}
    }}
    """
    
    # Get model for content optimization
    model = openrouter.get_content_model()
    
    try:
        # Send to OpenRouter for optimization
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are a content editing expert who specializes in improving article readability, engagement, and structure. Make meaningful improvements while preserving the original content's intent, information, and tone.",
            temperature=0.4  # Lower temperature for more precise edits
        )
        
        if not response:
            logger.error("Failed to optimize article readability")
            return content, {"error": "Optimization failed"}
        
        # Extract optimized content and analysis
        optimized_content = response.get("optimized_content", content)
        analysis = response.get("analysis", {})
        
        return optimized_content, analysis
    except Exception as e:
        logger.error(f"Error optimizing article readability: {str(e)}")
        return content, {"error": str(e)}