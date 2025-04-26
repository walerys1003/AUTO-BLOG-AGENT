"""
Google Trends integration module
"""
import logging
from pytrends.request import TrendReq
import pandas as pd

# Setup logging
logger = logging.getLogger(__name__)

class GoogleTrends:
    """Google Trends API client"""
    def __init__(self, hl='pl-PL', tz=360):
        """
        Initialize Google Trends client
        
        Args:
            hl: Language (default: 'pl-PL')
            tz: Timezone (default: 360)
        """
        self.pytrends = TrendReq(hl=hl, tz=tz)
        logger.info("Google Trends API client initialized")
    
    def get_daily_trends(self, country='poland', limit=10):
        """
        Get daily trending searches
        
        Args:
            country: Country code (default: 'poland')
            limit: Maximum number of trends to return (default: 10)
            
        Returns:
            list: List of trending search terms
        """
        try:
            logger.info(f"Fetching daily trends for {country}")
            # Build payload with dummy keyword (required)
            self.pytrends.build_payload(kw_list=['news'], timeframe='now 1-d')
            
            # Get trending searches for specified country
            trending_searches_df = self.pytrends.trending_searches(pn=country)
            
            # Convert to list and limit results
            trends = trending_searches_df[0][:limit].tolist()
            
            logger.info(f"Found {len(trends)} trending searches")
            return trends
        except Exception as e:
            logger.error(f"Error fetching daily trends: {str(e)}")
            return []
    
    def get_related_queries(self, keyword, country='PL'):
        """
        Get related queries for a keyword
        
        Args:
            keyword: Keyword to find related queries for
            country: Country code (default: 'PL')
            
        Returns:
            list: List of related queries
        """
        try:
            logger.info(f"Fetching related queries for '{keyword}' in {country}")
            
            # Build payload with the keyword
            self.pytrends.build_payload(kw_list=[keyword], geo=country, timeframe='today 12-m')
            
            # Get related queries
            related_queries = self.pytrends.related_queries()
            
            # Extract rising queries if available
            if keyword in related_queries and 'rising' in related_queries[keyword]:
                rising_df = related_queries[keyword]['rising']
                if not rising_df.empty:
                    queries = rising_df['query'].tolist()
                    logger.info(f"Found {len(queries)} related rising queries")
                    return queries
            
            # Extract top queries if rising not available
            if keyword in related_queries and 'top' in related_queries[keyword]:
                top_df = related_queries[keyword]['top']
                if not top_df.empty:
                    queries = top_df['query'].tolist()
                    logger.info(f"Found {len(queries)} related top queries")
                    return queries
            
            logger.warning(f"No related queries found for '{keyword}'")
            return []
        except Exception as e:
            logger.error(f"Error fetching related queries for '{keyword}': {str(e)}")
            return []
    
    def get_interest_over_time(self, keywords, timeframe='today 12-m', country='PL'):
        """
        Get interest over time for keywords
        
        Args:
            keywords: List of keywords
            timeframe: Time period (default: 'today 12-m')
            country: Country code (default: 'PL')
            
        Returns:
            dict: Dictionary with keywords as keys and interest values as values
        """
        if not keywords:
            return {}
        
        try:
            logger.info(f"Fetching interest over time for {len(keywords)} keywords")
            
            # Limit to 5 keywords (Google Trends API limit)
            keywords = keywords[:5]
            
            # Build payload with keywords
            self.pytrends.build_payload(kw_list=keywords, geo=country, timeframe=timeframe)
            
            # Get interest over time
            interest_over_time_df = self.pytrends.interest_over_time()
            
            # Calculate mean interest for each keyword
            result = {}
            for keyword in keywords:
                if keyword in interest_over_time_df.columns:
                    result[keyword] = interest_over_time_df[keyword].mean()
                else:
                    result[keyword] = 0
            
            logger.info(f"Successfully retrieved interest data for {len(result)} keywords")
            return result
        except Exception as e:
            logger.error(f"Error fetching interest over time: {str(e)}")
            return {keyword: 0 for keyword in keywords}


# Create default instance
default_client = GoogleTrends()

# Convenience functions using default client
def get_daily_trends(country='poland', limit=10):
    """Get daily trending searches using default client"""
    return default_client.get_daily_trends(country, limit)

def get_related_queries(keyword, country='PL'):
    """Get related queries for a keyword using default client"""
    return default_client.get_related_queries(keyword, country)

def get_interest_over_time(keywords, timeframe='today 12-m', country='PL'):
    """Get interest over time for keywords using default client"""
    return default_client.get_interest_over_time(keywords, timeframe, country)