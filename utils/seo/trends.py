"""
Google Trends Integration

This module provides functions to interact with Google Trends data.
"""

import logging
import json
import time
import random
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

# If import fails, we'll use our custom PatchedTrendReq implementation
try:
    # Try import original pytrends
    from utils.seo.patched_trends import PatchedTrendReq
    logger.info("Using PatchedTrendReq for Google Trends API")
except ImportError:
    # Fallback to our custom implementation
    logger.warning("Could not import PatchedTrendReq, using built-in fallback")
    # Define a simpler fallback trend implementation
    class PatchedTrendReq:
        def __init__(self, hl='en-US', tz=360, geo='', timeout=(2, 5), proxies='',
                    retries=0, backoff_factor=0, requests_args=None):
            self.hl = hl
            self.geo = geo
            
        def trending_searches(self, pn='poland'):
            """Fallback trending searches data"""
            fallback_trends = get_fallback_trends(pn)
            return fallback_trends
            
        def today_searches(self, pn='PL'):
            """Get today's trending searches"""
            fallback_trends = get_fallback_trends(pn)
            return [{"title": {"query": t}} for t in fallback_trends]
            
        def interest_over_time(self):
            """Fallback interest over time data"""
            return {
                "data": {
                    "timestamp": [int(datetime.now().timestamp()) - i * 86400 for i in range(30)],
                    "values": [random.randint(20, 100) for _ in range(30)]
                }
            }
            
        def related_topics(self):
            """Fallback related topics data"""
            return {
                "rising": [
                    {"topic_title": f"Related Topic {i}", "value": random.randint(1, 100)} 
                    for i in range(1, 6)
                ]
            }
        
        def build_payload(self, kw_list, timeframe='today 12-m', geo=''):
            """Build payload for trend requests"""
            self.kw_list = kw_list
            self.geo = geo or self.geo
            return True


def get_daily_trends(country="pl"):
    """
    Get daily trends from Google Trends.
    
    Args:
        country: The country code (default: 'pl' for Poland)
        
    Returns:
        List of trending search terms
    """
    try:
        logger.info(f"Fetching daily trends for {country}")
        pytrend = PatchedTrendReq(hl=f'pl-{country.upper()}')
        
        # Map country code to Google Trends country name
        country_map = {
            'pl': 'poland',
            'us': 'united_states',
            'uk': 'united_kingdom',
            'de': 'germany',
            'fr': 'france',
            'es': 'spain',
            'it': 'italy'
        }
        country_name = country_map.get(country.lower(), 'poland')
        
        # Get trending searches for the country
        trending = pytrend.trending_searches(pn=country_name)
        
        # Extract the trending topics
        if isinstance(trending, list) and len(trending) > 0:
            # If the data is returned as expected
            return trending[:20]  # Limit to top 20
        else:
            # Fallback to default topics
            logger.warning(f"Unexpected response format from Google Trends: {trending}")
            return get_fallback_trends(country)
            
    except Exception as e:
        logger.error(f"Error fetching daily trends: {str(e)}")
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
    try:
        pytrend = PatchedTrendReq(hl=f'pl-{country.upper()}')
        pytrend.build_payload([keyword], timeframe=timeframe, geo=country.upper())
        related_topics = pytrend.related_topics()
        
        if keyword in related_topics and 'rising' in related_topics[keyword]:
            return related_topics[keyword]['rising'][:10]
        else:
            logger.warning(f"No related topics found for {keyword}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting related topics for {keyword}: {str(e)}")
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
    daily_trends = get_daily_trends(country)
    
    # Extract just the trend names
    if isinstance(daily_trends, list):
        if daily_trends and isinstance(daily_trends[0], str):
            # Already strings
            return daily_trends[:limit]
        elif daily_trends and isinstance(daily_trends[0], dict) and 'title' in daily_trends[0]:
            # Extract from title.query format
            return [trend.get('title', {}).get('query', '') for trend in daily_trends if trend.get('title', {}).get('query')][:limit]
        elif daily_trends and isinstance(daily_trends[0], dict) and 'query' in daily_trends[0]:
            # Extract from query format
            return [trend.get('query', '') for trend in daily_trends if trend.get('query')][:limit]
    
    # Fallback to default topics
    logger.warning(f"Could not parse trends data. Using fallback trends.")
    return get_fallback_trends(country)[:limit]


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
    try:
        pytrend = PatchedTrendReq(hl=f'pl-{country.upper()}')
        pytrend.build_payload([keyword], timeframe=timeframe, geo=country.upper())
        interest_over_time_df = pytrend.interest_over_time()
        
        if isinstance(interest_over_time_df, dict) and 'data' in interest_over_time_df:
            # Our custom implementation returns dict
            return interest_over_time_df['data']
        
        # Convert pandas DataFrame to dict
        result = {}
        for col in interest_over_time_df.columns:
            if col != 'isPartial':
                result[col] = interest_over_time_df[col].to_list()
        
        # Add timestamps
        result['timestamp'] = interest_over_time_df.index.astype(int).to_list() // 10**9
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting interest over time for {keyword}: {str(e)}")
        
        # Return fallback data
        timestamps = [int((datetime.now() - timedelta(days=i)).timestamp()) for i in range(30)]
        values = [random.randint(20, 100) for _ in range(30)]
        
        return {
            'timestamp': timestamps,
            keyword: values
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
    # Default trends for Poland (pl)
    pl_trends = [
        "Zakupy online", 
        "Pogoda dziś", 
        "Koronawirus statystyki", 
        "Liga Mistrzów", 
        "Notowania giełdowe",
        "Najnowsze filmy", 
        "Przepisy kulinarne", 
        "Suplementy diety", 
        "Zdrowe odżywianie", 
        "Ćwiczenia w domu",
        "Samochody elektryczne", 
        "Ceny mieszkań", 
        "Kredyt hipoteczny", 
        "Podróże last minute", 
        "Telefony komórkowe",
        "Szczepionka COVID", 
        "Problemy ze snem", 
        "Praca zdalna", 
        "Kursy online", 
        "Oszczędzanie pieniędzy"
    ]
    
    # English trends for other countries
    en_trends = [
        "Online shopping", 
        "Weather today", 
        "COVID statistics", 
        "Champions League", 
        "Stock market",
        "Latest movies", 
        "Cooking recipes", 
        "Dietary supplements", 
        "Healthy eating", 
        "Home workouts",
        "Electric cars", 
        "Housing prices", 
        "Mortgage rates", 
        "Last minute travel", 
        "Smartphones",
        "COVID vaccine", 
        "Sleep problems", 
        "Remote work", 
        "Online courses", 
        "Money saving tips"
    ]
    
    # German trends
    de_trends = [
        "Online-Shopping", 
        "Wetter heute", 
        "Corona Statistik", 
        "Champions League", 
        "Aktienmarkt",
        "Neue Filme", 
        "Kochrezepte", 
        "Nahrungsergänzungsmittel", 
        "Gesunde Ernährung", 
        "Heimtraining",
        "Elektroautos", 
        "Immobilienpreise", 
        "Hypothekenzinsen", 
        "Last-Minute-Reisen", 
        "Smartphones",
        "Corona-Impfstoff", 
        "Schlafprobleme", 
        "Homeoffice", 
        "Online-Kurse", 
        "Geld sparen"
    ]
    
    # Select trends based on country
    if country.lower() == 'pl':
        return pl_trends
    elif country.lower() == 'de':
        return de_trends
    else:
        return en_trends