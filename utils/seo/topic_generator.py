"""
Topic Generator

This module provides functions for generating article topics from trends and keywords.
"""
import logging
import json
import time
import random
from datetime import datetime
from config import Config
from utils.seo.serp import get_serp_data, analyze_serp_results
from utils.seo.trends import get_daily_trends, get_related_topics

# Setup logging
logger = logging.getLogger(__name__)

# Category mapping for better topic categorization
CATEGORY_MAPPING = {
    'biznes': ['finanse', 'inwestycje', 'przedsiębiorstwo', 'zarządzanie', 'firma', 'marketing'],
    'technologia': ['ai', 'internet', 'programowanie', 'cyberbezpieczeństwo', 'komputery', 'aplikacje'],
    'zdrowie': ['medycyna', 'dieta', 'fitness', 'wellness', 'choroba', 'leczenie'],
    'edukacja': ['nauka', 'szkoła', 'uniwersytet', 'kształcenie', 'szkolenia', 'e-learning'],
    'rozrywka': ['gry', 'filmy', 'muzyka', 'sport', 'podróże', 'hobby'],
    'IT': ['programowanie', 'sieć', 'cyberbezpieczeństwo', 'cloud', 'software', 'hardware'],
    'transport': ['samochody', 'logistyka', 'pojazdy', 'przewóz', 'elektryczne'],
    'medycyna': ['leczenie', 'szpital', 'opieka', 'lekarze', 'choroby', 'terapia'],
    'finanse': ['inwestycje', 'oszczędności', 'podatki', 'kredyty', 'bank', 'waluta']
}

def generate_topics_from_trends(trends, categories=None, blog_id=None, limit=5):
    """
    Generate article topics from trending searches.
    
    Args:
        trends: List of trending search terms
        categories: List of categories to filter by
        blog_id: ID of the blog to generate topics for
        limit: Maximum number of topics to generate (default: 5)
        
    Returns:
        List of generated topics
    """
    logger.info(f"Generating topics from {len(trends)} trends")
    
    topics = []
    
    try:
        # Process each trend
        for trend in trends[:10]:  # Limit to top 10 trends
            logger.info(f"Processing trend: '{trend}'")
            
            # Check if trend matches any category
            if categories:
                matches_category = False
                
                for category in categories:
                    category_lower = category.lower()
                    
                    # Check direct match
                    if category_lower in trend.lower():
                        matches_category = True
                        break
                    
                    # Check match with related terms
                    if category_lower in CATEGORY_MAPPING:
                        for related_term in CATEGORY_MAPPING[category_lower]:
                            if related_term in trend.lower():
                                matches_category = True
                                break
                
                if not matches_category:
                    logger.info(f"Trend '{trend}' does not match any selected category")
                    continue
            
            # Get SERP data for the trend
            serp_data = get_serp_data(trend)
            
            if not serp_data:
                logger.warning(f"No SERP data found for trend: '{trend}'")
                continue
            
            # Analyze SERP results
            analysis = analyze_serp_results(serp_data)
            
            if not analysis:
                logger.warning(f"Failed to analyze SERP results for trend: '{trend}'")
                continue
            
            # Generate topics based on SERP analysis
            generated = generate_topic_variations(trend, analysis, categories)
            
            if generated:
                topics.extend(generated)
                
                # Check if we have enough topics
                if len(topics) >= limit:
                    break
        
        # If we still don't have enough topics, generate some from keywords
        if len(topics) < limit and trends:
            # Get related topics for the top trend
            related = get_related_topics(trends[0])
            
            if related:
                for topic in related[:5]:
                    if len(topics) >= limit:
                        break
                    
                    title = topic.get('title', '')
                    
                    if title and not any(t['title'] == title for t in topics):
                        # Generate a topic from the related topic
                        topics.append({
                            'title': title,
                            'score': 60,
                            'keywords': [title],
                            'category': get_best_category(title, categories),
                            'blog_id': blog_id
                        })
        
        # Prioritize topics
        topics = sorted(topics, key=lambda x: x.get('score', 0), reverse=True)
        
        return topics[:limit]
        
    except Exception as e:
        logger.error(f"Error generating topics from trends: {str(e)}")
        return []

def generate_topic_variations(trend, serp_analysis, categories=None):
    """
    Generate topic variations based on a trend and SERP analysis.
    
    Args:
        trend: The trend term
        serp_analysis: SERP analysis data
        categories: List of categories to filter by
        
    Returns:
        List of generated topic variations
    """
    variations = []
    
    try:
        # Get current date for more relevant titles
        current_year = datetime.now().year
        current_month = datetime.now().strftime("%B")
        
        # Extract keywords from SERP analysis
        keywords = serp_analysis.get('top_keywords', [])
        
        # Generate a standard "how to" topic
        variations.append({
            'title': f"Jak {trend.lower()} może pomóc w rozwoju Twojej firmy w {current_year} roku",
            'score': 85,
            'keywords': [trend] + keywords[:3],
            'category': get_best_category(trend, categories),
            'format': 'how-to'
        })
        
        # Generate a list-based topic
        variations.append({
            'title': f"10 najważniejszych faktów o {trend.lower()}, które musisz znać w {current_year} roku",
            'score': 80,
            'keywords': [trend] + keywords[:3],
            'category': get_best_category(trend, categories),
            'format': 'listicle'
        })
        
        # Generate a guide topic
        variations.append({
            'title': f"Kompletny przewodnik po {trend.lower()}: wszystko, co musisz wiedzieć",
            'score': 75,
            'keywords': [trend] + keywords[:3],
            'category': get_best_category(trend, categories),
            'format': 'guide'
        })
        
        # Generate a comparison topic
        if keywords and len(keywords) >= 2:
            variations.append({
                'title': f"{trend.capitalize()} vs {keywords[0].capitalize()}: co jest lepsze dla Twojej firmy?",
                'score': 70,
                'keywords': [trend, keywords[0]] + keywords[1:3],
                'category': get_best_category(trend, categories),
                'format': 'comparison'
            })
        
        # Generate a case study topic
        variations.append({
            'title': f"Case study: Jak firma zwiększyła zyski o 50% dzięki {trend.lower()}",
            'score': 65,
            'keywords': [trend] + keywords[:3],
            'category': get_best_category(trend, categories),
            'format': 'case-study'
        })
        
        return variations
        
    except Exception as e:
        logger.error(f"Error generating topic variations: {str(e)}")
        return []

def get_best_category(topic, available_categories=None):
    """
    Determine the best category for a topic.
    
    Args:
        topic: The topic to categorize
        available_categories: List of available categories
        
    Returns:
        Best matching category
    """
    topic_lower = topic.lower()
    
    if not available_categories:
        available_categories = list(CATEGORY_MAPPING.keys())
    
    # Check direct matches
    for category in available_categories:
        category_lower = category.lower()
        
        if category_lower in topic_lower:
            return category
    
    # Check matches with related terms
    for category in available_categories:
        category_lower = category.lower()
        
        if category_lower in CATEGORY_MAPPING:
            for related_term in CATEGORY_MAPPING[category_lower]:
                if related_term in topic_lower:
                    return category
    
    # Return default category
    return random.choice(available_categories) if available_categories else "Ogólne"