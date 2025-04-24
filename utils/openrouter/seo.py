import logging
import json
import time
from typing import List, Dict, Any, Optional
from utils.openrouter import openrouter
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

def analyze_trends_for_keywords(keywords: List[str], niche: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze search volume and competition for a list of keywords
    
    Args:
        keywords: List of keywords to analyze
        niche: Optional niche/industry for context
        
    Returns:
        Dictionary with analysis results
    """
    if not keywords:
        logger.warning("No keywords provided for analysis")
        return {
            "success": False,
            "message": "No keywords provided",
            "data": {}
        }
    
    # Build the prompt for trend analysis
    keywords_text = ", ".join(keywords)
    niche_context = f" in the {niche} industry" if niche else ""
    
    prompt = f"""
    Perform a search trend analysis for the following keywords{niche_context}: {keywords_text}
    
    For each keyword, provide:
    1. Estimated search volume (high, medium, low)
    2. Competition level (high, medium, low)
    3. Trending status (rising, stable, declining)
    4. Seasonal factors (if any)
    5. Suggested related keywords with lower competition
    
    Format your response as a JSON object with the following structure:
    {{
        "keywords": [
            {{
                "keyword": "keyword1",
                "search_volume": "high|medium|low",
                "competition": "high|medium|low",
                "trend": "rising|stable|declining",
                "seasonal_factors": "any seasonal patterns or null",
                "related_keywords": ["keyword1", "keyword2"]
            }},
            ...
        ],
        "overview": "general insights about these keywords as a group",
        "recommendations": "strategic recommendations for content creation"
    }}
    """
    
    # Get model for SEO analysis
    model = openrouter.get_topic_model()
    
    try:
        # Send to OpenRouter for analysis
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are an SEO expert who specializes in keyword research and trend analysis. Provide accurate, data-driven insights about keyword trends, search volume, and competition levels. Be specific and analytical in your assessment.",
            temperature=0.3
        )
        
        if not response:
            logger.error("Failed to get trend analysis response")
            return {
                "success": False,
                "message": "Failed to analyze trends",
                "data": {}
            }
        
        return {
            "success": True,
            "message": "Trend analysis completed",
            "data": response
        }
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}")
        return {
            "success": False, 
            "message": f"Error: {str(e)}",
            "data": {}
        }

def generate_seo_optimized_topics(
    niche: str, 
    keywords: Optional[List[str]] = None,
    count: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate SEO-optimized topic ideas based on niche and keywords
    
    Args:
        niche: The blog niche or industry
        keywords: Optional list of target keywords
        count: Number of topics to generate
        
    Returns:
        List of topic dictionaries with title, keywords, and score
    """
    keywords_text = ""
    if keywords and len(keywords) > 0:
        keywords_text = f"Target keywords to incorporate: {', '.join(keywords)}\n"
    
    prompt = f"""
    Generate {count} SEO-optimized blog post topics for a blog in the {niche} niche.
    {keywords_text}
    For each topic:
    1. Create an engaging, click-worthy title that also includes SEO keywords
    2. Suggest 3-5 primary keywords to target in the content
    3. Assign a category that best fits the topic
    4. Include an SEO competitiveness score (0.0-1.0) where lower means less competition
    
    Format your response as a JSON array with the following structure for each topic:
    [
        {{
            "title": "The Complete Guide to [Topic]",
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "category": "category name",
            "score": 0.5
        }},
        ...
    ]
    """
    
    # Get model for topic generation
    model = openrouter.get_topic_model()
    
    try:
        # Send to OpenRouter for topic generation
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are an SEO content strategist who specializes in creating high-performing blog content that ranks well in search engines. Generate engaging, SEO-optimized topics that have a good balance of search volume, low competition, and high reader interest.",
            temperature=0.7
        )
        
        if not response or not isinstance(response, list):
            logger.error("Failed to generate topics or invalid response format")
            return []
        
        return response
    except Exception as e:
        logger.error(f"Error generating SEO topics: {str(e)}")
        return []

def analyze_content_seo_performance(
    title: str,
    content: str,
    keywords: List[str]
) -> Dict[str, Any]:
    """
    Analyze content for SEO performance and provide recommendations
    
    Args:
        title: Content title
        content: The full content text
        keywords: Target keywords for the content
        
    Returns:
        Dictionary with SEO analysis and recommendations
    """
    keywords_text = ", ".join(keywords)
    content_sample = content[:3000] + "..." if len(content) > 3000 else content
    
    prompt = f"""
    Perform an SEO analysis of the following content:
    
    Title: {title}
    Target Keywords: {keywords_text}
    
    Content Sample:
    {content_sample}
    
    Analyze for:
    1. Keyword density and placement
    2. Content readability and structure
    3. Meta description quality
    4. Header tag usage
    5. Internal and external linking opportunities
    6. Overall SEO score (0-100)
    
    Format your response as a JSON object with the following structure:
    {{
        "seo_score": 75,
        "keyword_analysis": {{
            "primary_keyword_density": 0.02,
            "secondary_keyword_presence": true,
            "keyword_in_title": true,
            "keyword_in_headers": true
        }},
        "readability": {{
            "score": "good|medium|poor",
            "issues": ["issue1", "issue2"]
        }},
        "structure": {{
            "header_usage": "good|medium|poor",
            "paragraph_length": "good|medium|poor"
        }},
        "recommendations": [
            "recommendation1",
            "recommendation2"
        ]
    }}
    """
    
    # Get model for content analysis
    model = openrouter.get_content_model()
    
    try:
        # Send to OpenRouter for analysis
        response = openrouter.generate_json_response(
            prompt=prompt,
            model=model,
            system_prompt="You are an SEO content optimizer who specializes in analyzing content for search engine performance. Provide detailed, actionable insights on how to improve content for better search rankings.",
            temperature=0.3
        )
        
        if not response:
            logger.error("Failed to analyze content SEO performance")
            return {
                "success": False,
                "message": "Failed to analyze content",
                "data": {}
            }
        
        return {
            "success": True,
            "message": "Content analysis completed",
            "data": response
        }
    except Exception as e:
        logger.error(f"Error analyzing content SEO: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": {}
        }