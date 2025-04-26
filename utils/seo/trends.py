"""
Google Trends Integration

This module provides functions to interact with Google Trends data.
"""
import logging
import requests
import json
import random
from datetime import datetime, timedelta
from pytrends.request import TrendReq

# Setup logging
logger = logging.getLogger(__name__)

def get_daily_trends(country="pl"):
    """
    Get daily trends from Google Trends.
    
    Args:
        country: The country code (default: 'pl' for Poland)
        
    Returns:
        List of trending search terms
    """
    logger.info(f"Fetching daily trends for {country}")
    
    try:
        # Initialize pytrends with updated parameters
        pytrends = TrendReq(hl=f'{country}-{country.upper()}', timeout=(10, 25), 
                          retries=2, backoff_factor=0.1,
                          requests_args={'verify': True})
        
        # Get daily trends data
        daily_trends = pytrends.trending_searches(pn=country)
        
        # Extract trending terms
        if not daily_trends.empty:
            trends = daily_trends[0].tolist()
            return trends
        else:
            logger.warning(f"No daily trends found for {country}")
            # Return a list of fallback trends in case we can't get real data
            # (this happens due to API limits)
            return get_fallback_trends(country)
            
    except Exception as e:
        logger.error(f"Error fetching daily trends: {str(e)}")
        # Return fallback trends on error
        return get_fallback_trends(country)

def get_related_topics(keyword, country="pl", timeframe="today 12-m"):
    """
    Get topics related to a keyword.
    
    Args:
        keyword: The keyword to get related topics for
        country: The country code (default: 'pl')
        timeframe: Time frame for the data (default: 'today 12-m')
        
    Returns:
        Dictionary of related topics
    """
    logger.info(f"Fetching related topics for '{keyword}' in {country}")
    
    try:
        # Initialize pytrends with updated parameters
        pytrends = TrendReq(hl=f'{country}-{country.upper()}',
                          requests_args={'verify': True})
        
        # Build payload
        pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=country.upper())
        
        # Get related topics
        related_topics = pytrends.related_topics()
        
        if keyword in related_topics and not related_topics[keyword].empty:
            # Extract top related topics
            top_topics = related_topics[keyword]['top']
            topics = []
            
            if not top_topics.empty:
                for _, row in top_topics.iterrows():
                    topics.append({
                        'title': row.get('topic_title', ''),
                        'type': row.get('topic_type', ''),
                        'value': float(row.get('value', 0))
                    })
            
            return topics
        else:
            logger.warning(f"No related topics found for '{keyword}'")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching related topics: {str(e)}")
        return []

def get_trending_topics(country="pl", limit=10):
    """
    Get trending topics for content creation.
    
    Args:
        country: The country code (default: 'pl')
        limit: Maximum number of topics to return (default: 10)
        
    Returns:
        List of trending topics
    """
    logger.info(f"Fetching trending topics for {country}")
    
    trending_topics = []
    
    # Get daily trends
    daily_trends = get_daily_trends(country)
    
    # Limit results
    if daily_trends:
        trending_topics = daily_trends[:limit]
    
    return trending_topics

def get_interest_over_time(keyword, country="pl", timeframe="today 12-m"):
    """
    Get interest over time for a keyword.
    
    Args:
        keyword: The keyword to get interest data for
        country: The country code (default: 'pl')
        timeframe: Time frame for the data (default: 'today 12-m')
        
    Returns:
        Dictionary with interest over time data
    """
    logger.info(f"Fetching interest over time for '{keyword}' in {country}")
    
    try:
        # Initialize pytrends with updated parameters
        pytrends = TrendReq(hl=f'{country}-{country.upper()}',
                          requests_args={'verify': True})
        
        # Build payload
        pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=country.upper())
        
        # Get interest over time
        interest_df = pytrends.interest_over_time()
        
        if not interest_df.empty:
            # Convert dataframe to dictionary
            interest_data = []
            
            for date, row in interest_df.iterrows():
                if keyword in row:
                    interest_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'value': int(row[keyword])
                    })
            
            return {
                'keyword': keyword,
                'data': interest_data
            }
        else:
            logger.warning(f"No interest data found for '{keyword}'")
            return {
                'keyword': keyword,
                'data': []
            }
            
    except Exception as e:
        logger.error(f"Error fetching interest over time: {str(e)}")
        return {
            'keyword': keyword,
            'data': []
        }

def get_fallback_trends(country="pl"):
    """
    Get fallback trends when Google Trends API is rate-limited.
    This ensures we always have some trends to work with.
    
    Args:
        country: The country code to get fallback trends for
        
    Returns:
        List of trending search terms
    """
    # Poland-specific fallback trends for different categories
    pl_trends = [
        # Technology
        "nowy iPhone", "sztuczna inteligencja", "ChatGPT", "Android 15", 
        "najnowsze smartfony", "technologie przyszłości", "Starlink",
        
        # Business
        "inwestowanie w złoto", "GPW", "kursy walut", "podwyżki stóp procentowych",
        "inflacja", "kredyt hipoteczny", "dofinansowanie dla firm",
        
        # Health
        "zdrowy tryb życia", "dieta śródziemnomorska", "naturalne suplementy",
        "ćwiczenia w domu", "zdrowe odżywianie", "joga",
        
        # Entertainment
        "nowe seriale Netflix", "premiery filmowe", "koncerty 2025",
        "festiwale muzyczne", "najlepsze książki", "gry komputerowe",
        
        # Travel
        "wakacje all-inclusive", "podróże po Polsce", "tanie loty",
        "najpiękniejsze plaże", "zimowe wyjazdy", "agroturystyka",
        
        # Home
        "urządzanie mieszkania", "nowoczesne wnętrza", "meble DIY",
        "oszczędzanie energii", "fotowoltaika", "pompy ciepła",
        
        # Food
        "przepisy na obiad", "kuchnia roślinna", "keto dieta",
        "domowe wypieki", "slow food", "bezglutenowe przepisy"
    ]
    
    # Return 10 random trends from the list
    random.shuffle(pl_trends)
    return pl_trends[:10]