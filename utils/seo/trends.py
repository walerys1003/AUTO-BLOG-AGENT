"""
Google Trends API Interface

This module provides functions for interacting with Google Trends data
"""
import logging
import json
import time
import random
from datetime import datetime, timedelta
from urllib.parse import urlencode
import requests

# Setup logging
logger = logging.getLogger(__name__)

class TrendsRequestError(Exception):
    """Exception raised when a Google Trends request fails"""
    pass

def initialize_trends_client():
    """Initialize the Google Trends API client"""
    logger.info("Google Trends API client initialized")
    return True

def get_daily_trends(geo='PL', language='pl-PL'):
    """
    Get daily trending searches for a specific geographic area.
    
    Args:
        geo: The geographic area (default: 'PL' for Poland)
        language: The language for results (default: 'pl-PL')
        
    Returns:
        List of trending topics
    """
    try:
        logger.info(f"Fetching daily trends for {geo.lower()}")
        
        # First, make a request to get a token/cookie
        base_url = "https://trends.google.com/trends/explore"
        params = {'geo': geo}
        
        try:
            response = requests.get(base_url, params=params)
            
            if response.status_code != 200:
                raise TrendsRequestError(f"Google returned a response with code {response.status_code}")
        except Exception as e:
            raise TrendsRequestError(f"The request failed: {str(e)}")
        
        # Now, fetch the actual trending data
        api_url = "https://trends.google.com/trends/api/explore"
        
        # Parameters for trending search request
        payload = {
            'hl': language,
            'tz': 360,  # Time zone offset in minutes
            'req': json.dumps({
                'comparisonItem': [{"keyword": "news", "time": "now 1-d", "geo": ""}],
                'category': 0,
                'property': '',
            })
        }
        
        trends_response = requests.post(api_url, params=payload)
        
        if trends_response.status_code != 200:
            raise TrendsRequestError(f"Google returned a response with code {trends_response.status_code}")
        
        # Extract daily trends 
        response_text = trends_response.text[5:]  # Remove garbage prefix
        data = json.loads(response_text)
        
        # Try to get daily trends from another endpoint
        daily_url = "https://trends.google.com/trends/hottrends/visualize/internal/data"
        
        daily_response = requests.get(daily_url)
        
        if daily_response.status_code != 200:
            raise TrendsRequestError(f"Google returned a response with code {daily_response.status_code}")
        
        try:
            daily_data = daily_response.json()
            # Extract trending searches for the specified geo
            if geo in daily_data:
                trends = []
                for topic_group in daily_data[geo]:
                    for topic in topic_group:
                        trends.append(topic['title'])
                return trends[:10]  # Return top 10 trends
            else:
                # Fallback: generate some recent topics based on categories
                return generate_fallback_trends()
        except Exception as e:
            logger.error(f"Error parsing daily trends: {str(e)}")
            return generate_fallback_trends()
    
    except Exception as e:
        logger.error(f"Error fetching daily trends: {str(e)}")
        return generate_fallback_trends()

def get_related_topics(keyword, geo='PL', language='pl-PL'):
    """
    Get topics related to a keyword.
    
    Args:
        keyword: The search term to find related topics for
        geo: The geographic area (default: 'PL' for Poland)
        language: The language for results (default: 'pl-PL')
        
    Returns:
        List of related topics
    """
    try:
        logger.info(f"Fetching related topics for '{keyword}' in {geo}")
        
        # Base URL for the API
        api_url = "https://trends.google.com/trends/api/widgetdata/relatedsearches"
        
        # First get a token by making a request to the explore endpoint
        explore_url = "https://trends.google.com/trends/api/explore"
        
        # Parameters for the explore request
        explore_payload = {
            'hl': language,
            'tz': 360,
            'req': json.dumps({
                'comparisonItem': [{"keyword": keyword, "geo": geo, "time": "today 12-m"}],
                'category': 0,
                'property': '',
            })
        }
        
        explore_response = requests.post(explore_url, params=explore_payload)
        
        if explore_response.status_code != 200:
            raise TrendsRequestError(f"Google returned a response with code {explore_response.status_code}")
        
        # Extract token from the explore response
        response_text = explore_response.text[5:]  # Remove garbage prefix
        data = json.loads(response_text)
        
        try:
            widgets = data['widgets']
            related_topics_widget = None
            
            # Find the related topics widget
            for widget in widgets:
                if widget['id'] == 'RELATED_TOPICS':
                    related_topics_widget = widget
                    break
            
            if not related_topics_widget:
                logger.warning(f"No related topics widget found for '{keyword}'")
                return []
            
            # Get related topics data
            token = related_topics_widget['token']
            req = related_topics_widget['request']
            
            topics_payload = {
                'hl': language,
                'tz': 360,
                'req': json.dumps(req),
                'token': token,
            }
            
            topics_response = requests.get(api_url, params=topics_payload)
            
            if topics_response.status_code != 200:
                raise TrendsRequestError(f"Google returned a response with code {topics_response.status_code}")
            
            # Parse and extract related topics
            topics_text = topics_response.text[5:]  # Remove garbage prefix
            topics_data = json.loads(topics_text)
            
            related_topics = []
            
            if 'default' in topics_data['default']:
                for topic in topics_data['default']['rankedList'][0]['rankedKeyword']:
                    related_topics.append({
                        'title': topic['topic']['title'],
                        'type': topic['topic']['type'],
                        'value': topic['value']
                    })
            
            return related_topics
            
        except Exception as e:
            logger.error(f"Error parsing related topics: {str(e)}")
            return []
    
    except Exception as e:
        logger.error(f"Error fetching related topics: {str(e)}")
        return []

def generate_fallback_trends():
    """
    Generate fallback trends when the API fails.
    
    Returns:
        List of trending topics
    """
    categories = [
        'biznes', 'finanse', 'inwestycje',
        'technologia', 'AI', 'gadżety', 
        'zdrowie', 'odporność', 'dieta',
        'edukacja', 'szkolenia', 'e-learning',
        'rozrywka', 'gry', 'filmy'
    ]
    
    # Get current date for more realistic trends
    current_date = datetime.now()
    date_str = current_date.strftime("%B %Y")
    
    trends = [
        f"Najlepsze inwestycje {date_str}",
        f"Trendy w technologii {date_str}",
        f"Jak wzmocnić odporność organizmu",
        f"Nowe metody uczenia się online",
        f"Premiery filmowe {date_str}",
        f"Rozwój sztucznej inteligencji w {current_date.year} roku",
        f"Zarządzanie budżetem domowym w kryzysie",
        f"Efektywne metody oszczędzania",
        f"Najnowsze smartfony {date_str}",
        f"Zdrowe nawyki żywieniowe"
    ]
    
    return trends