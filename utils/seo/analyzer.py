"""
SEO Analyzer Module

This module provides functions for analyzing content for SEO optimization.
"""
import logging
import re
import json
from collections import Counter

# Setup logging
logger = logging.getLogger(__name__)

def analyze_content(content, primary_keyword, secondary_keywords=None):
    """
    Analyze content for SEO optimization.
    
    Args:
        content: The content to analyze
        primary_keyword: The primary keyword to check for
        secondary_keywords: List of secondary keywords to check for
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Analyzing content for primary keyword: {primary_keyword}")
    
    if not content:
        logger.warning("No content provided for analysis")
        return {
            'word_count': 0,
            'readability': {
                'score': 0,
                'level': 'Unknown',
                'sentences': 0,
                'avg_sentence_length': 0
            },
            'primary_keyword': {
                'count': 0,
                'density': 0,
                'in_title': False,
                'in_first_paragraph': False,
                'in_headings': False,
                'in_last_paragraph': False
            },
            'secondary_keywords': [],
            'headings': {
                'h1_count': 0,
                'h2_count': 0,
                'h3_count': 0,
                'h4_plus_count': 0
            },
            'recommendations': [
                "No content provided for analysis."
            ]
        }
    
    secondary_keywords = secondary_keywords or []
    
    # Normalize content
    content = content.strip()
    lowercase_content = content.lower()
    primary_keyword_lower = primary_keyword.lower()
    
    # Word count
    words = re.findall(r'\b\w+\b', content)
    word_count = len(words)
    
    # Keyword analysis
    primary_keyword_count = lowercase_content.count(primary_keyword_lower)
    primary_keyword_density = primary_keyword_count / word_count if word_count > 0 else 0
    
    # Split content into paragraphs
    paragraphs = content.split('\n\n')
    paragraphs = [p for p in paragraphs if p.strip()]
    
    # Check for keyword in first and last paragraphs
    in_first_paragraph = primary_keyword_lower in paragraphs[0].lower() if paragraphs else False
    in_last_paragraph = primary_keyword_lower in paragraphs[-1].lower() if paragraphs else False
    
    # Extract headings
    h1_pattern = re.compile(r'<h1[^>]*>(.*?)</h1>', re.IGNORECASE)
    h2_pattern = re.compile(r'<h2[^>]*>(.*?)</h2>', re.IGNORECASE)
    h3_pattern = re.compile(r'<h3[^>]*>(.*?)</h3>', re.IGNORECASE)
    h4_plus_pattern = re.compile(r'<h[4-6][^>]*>(.*?)</h[4-6]>', re.IGNORECASE)
    
    h1_tags = h1_pattern.findall(content)
    h2_tags = h2_pattern.findall(content)
    h3_tags = h3_pattern.findall(content)
    h4_plus_tags = h4_plus_pattern.findall(content)
    
    # Check if keyword is in headings
    in_headings = any(
        primary_keyword_lower in h.lower() 
        for h in h1_tags + h2_tags + h3_tags + h4_plus_tags
    )
    
    # Check if keyword is in title (assuming first h1 is title)
    in_title = primary_keyword_lower in h1_tags[0].lower() if h1_tags else False
    
    # Analyze secondary keywords
    secondary_keyword_analysis = []
    
    for keyword in secondary_keywords:
        if not keyword:
            continue
            
        keyword = keyword.lower()
        count = lowercase_content.count(keyword)
        density = count / word_count if word_count > 0 else 0
        
        secondary_keyword_analysis.append({
            'keyword': keyword,
            'count': count,
            'density': density,
            'in_content': count > 0
        })
    
    # Count sentences
    sentences = re.split(r'[.!?]+', content)
    sentences = [s for s in sentences if s.strip()]
    sentence_count = len(sentences)
    
    # Average sentence length
    if sentence_count > 0:
        avg_sentence_length = sum(len(re.findall(r'\b\w+\b', s)) for s in sentences) / sentence_count
    else:
        avg_sentence_length = 0
    
    # Calculate readability score (simplified Flesch-Kincaid)
    if sentence_count > 0 and word_count > 0:
        readability_score = 206.835 - (1.015 * (word_count / sentence_count)) - (84.6 * (sum(1 for w in words if len(w) > 2) / word_count))
        readability_score = max(0, min(100, readability_score))
    else:
        readability_score = 0
    
    # Determine readability level
    if readability_score >= 90:
        readability_level = "Very Easy"
    elif readability_score >= 80:
        readability_level = "Easy"
    elif readability_score >= 70:
        readability_level = "Fairly Easy"
    elif readability_score >= 60:
        readability_level = "Standard"
    elif readability_score >= 50:
        readability_level = "Fairly Difficult"
    elif readability_score >= 30:
        readability_level = "Difficult"
    else:
        readability_level = "Very Difficult"
    
    # Generate recommendations
    recommendations = []
    
    if word_count < 300:
        recommendations.append(f"Content is too short ({word_count} words). Aim for at least 500 words for better SEO.")
    
    if primary_keyword_density < 0.005:
        recommendations.append(f"Primary keyword density is too low ({primary_keyword_density:.1%}). Use the keyword more frequently.")
    elif primary_keyword_density > 0.03:
        recommendations.append(f"Primary keyword density is too high ({primary_keyword_density:.1%}). This might be seen as keyword stuffing.")
    
    if not in_title:
        recommendations.append("Include the primary keyword in the title (H1 tag).")
    
    if not in_first_paragraph:
        recommendations.append("Include the primary keyword in the first paragraph.")
    
    if not in_headings:
        recommendations.append("Include the primary keyword in at least one heading (H2, H3, etc.).")
    
    if not in_last_paragraph:
        recommendations.append("Consider including the primary keyword in the last paragraph for better SEO.")
    
    if not h2_tags:
        recommendations.append("No H2 headings found. Use H2 headings to structure your content.")
    
    if len(h1_tags) > 1:
        recommendations.append(f"Multiple H1 tags found ({len(h1_tags)}). Use only one H1 tag per page.")
    
    if h1_tags and h2_tags and len(h2_tags) < 2:
        recommendations.append("Too few H2 headings. Use more H2 headings to better structure your content.")
    
    if readability_score < 60:
        recommendations.append(f"Readability is {readability_level} ({readability_score:.1f}). Try to simplify your content.")
    
    if avg_sentence_length > 25:
        recommendations.append(f"Average sentence length is high ({avg_sentence_length:.1f} words). Consider using shorter sentences.")
    
    if word_count > 0 and len(secondary_keywords) > 0:
        secondary_keyword_coverage = sum(1 for kw in secondary_keyword_analysis if kw['in_content']) / len(secondary_keywords)
        if secondary_keyword_coverage < 0.7:
            recommendations.append(f"Only {secondary_keyword_coverage:.0%} of secondary keywords are used. Try to include more secondary keywords.")
    
    # Return analysis results
    return {
        'word_count': word_count,
        'readability': {
            'score': readability_score,
            'level': readability_level,
            'sentences': sentence_count,
            'avg_sentence_length': avg_sentence_length
        },
        'primary_keyword': {
            'count': primary_keyword_count,
            'density': primary_keyword_density,
            'in_title': in_title,
            'in_first_paragraph': in_first_paragraph,
            'in_headings': in_headings,
            'in_last_paragraph': in_last_paragraph
        },
        'secondary_keywords': secondary_keyword_analysis,
        'headings': {
            'h1_count': len(h1_tags),
            'h2_count': len(h2_tags),
            'h3_count': len(h3_tags),
            'h4_plus_count': len(h4_plus_tags)
        },
        'recommendations': recommendations
    }

def get_keyword_suggestions(topic, limit=5):
    """
    Get keyword suggestions for a topic.
    
    Args:
        topic: The topic to get suggestions for
        limit: Maximum number of suggestions to return (default: 5)
        
    Returns:
        List of keyword suggestions
    """
    logger.info(f"Getting keyword suggestions for topic: {topic}")
    
    try:
        # Get SERP data
        from .serp import get_serp_data
        serp_data = get_serp_data(topic)
        
        suggestions = []
        
        # Add the primary topic as a suggestion
        suggestions.append({
            'keyword': topic,
            'search_volume': 'High',
            'competition': 'Medium'
        })
        
        # Add related searches
        if 'related_searches' in serp_data:
            for i, search in enumerate(serp_data['related_searches'][:limit-1]):
                suggestions.append({
                    'keyword': search,
                    'search_volume': 'Medium',
                    'competition': 'Varies'
                })
                
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    except Exception as e:
        logger.error(f"Error getting keyword suggestions: {str(e)}")
        return [{'keyword': topic, 'search_volume': 'Unknown', 'competition': 'Unknown'}]

def initialize_seo_module():
    """Initialize the SEO analyzer module"""
    logger.info("Initializing SEO module")
    
    # Test Google Trends API
    try:
        from .trends import get_daily_trends
        trends = get_daily_trends()
        
        if trends:
            logger.info(f"Google Trends API test successful. Found {len(trends)} trends")
        else:
            logger.warning("Google Trends API test returned no trends")
    except Exception as e:
        logger.error(f"Error testing Google Trends API: {str(e)}")
    
    # Initialize SEO scheduler
    try:
        from .scheduler import initialize_seo_scheduler
        scheduler_initialized = initialize_seo_scheduler()
        
        if scheduler_initialized:
            logger.info("SEO scheduler initialized successfully")
        else:
            logger.warning("SEO scheduler initialization failed")
    except Exception as e:
        logger.error(f"Error initializing SEO scheduler: {str(e)}")
    
    logger.info("SEO module initialized successfully")
    return True