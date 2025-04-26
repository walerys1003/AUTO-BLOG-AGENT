"""
SerpAPI integration module
"""
import logging
import requests
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

class SerpApi:
    """SerpAPI client for fetching search results and related questions"""
    def __init__(self, api_key=None):
        """
        Initialize SerpAPI client
        
        Args:
            api_key: API key for SerpAPI (if None, uses Config.SERPAPI_KEY)
        """
        self.api_key = api_key or Config.SERPAPI_KEY
        if not self.api_key:
            logger.error("SerpAPI key is missing")
            raise ValueError("SerpAPI key is required")
        logger.info("SerpAPI client initialized")
        
        # Keep track of request count to avoid exceeding monthly limit
        self.request_count = 0
        self.MONTHLY_LIMIT = 100
    
    def search(self, keyword, location='Poland', lang='pl'):
        """
        Search for keyword and get related data
        
        Args:
            keyword: Search keyword
            location: Location for search (default: 'Poland')
            lang: Language code (default: 'pl')
            
        Returns:
            dict: Search results from SerpAPI
        """
        # Check if we've exceeded the monthly limit
        if self.request_count >= self.MONTHLY_LIMIT:
            logger.warning("Monthly SerpAPI request limit (100) reached")
            return {}
        
        try:
            logger.info(f"Searching SerpAPI for '{keyword}' in {location}")
            
            url = 'https://serpapi.com/search.json'
            params = {
                'q': keyword,
                'location': location,
                'hl': lang,
                'gl': lang,
                'api_key': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            self.request_count += 1  # Increment request counter
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully retrieved data for '{keyword}'")
                return data
            else:
                logger.error(f"SerpAPI error: {response.status_code}, {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error searching SerpAPI for '{keyword}': {str(e)}")
            return {}
    
    def get_related_questions(self, keyword, location='Poland', lang='pl', limit=5):
        """
        Get related questions for a keyword
        
        Args:
            keyword: Search keyword
            location: Location for search (default: 'Poland')
            lang: Language code (default: 'pl')
            limit: Maximum number of questions to return (default: 5)
            
        Returns:
            list: List of related questions
        """
        data = self.search(keyword, location, lang)
        
        if not data or 'related_questions' not in data:
            return []
        
        questions = [q['question'] for q in data['related_questions']]
        return questions[:limit]
    
    def get_top_results(self, keyword, location='Poland', lang='pl', limit=5):
        """
        Get top search results for a keyword
        
        Args:
            keyword: Search keyword
            location: Location for search (default: 'Poland')
            lang: Language code (default: 'pl')
            limit: Maximum number of results to return (default: 5)
            
        Returns:
            list: List of top search results
        """
        data = self.search(keyword, location, lang)
        
        if not data or 'organic_results' not in data:
            return []
        
        results = []
        for result in data['organic_results'][:limit]:
            results.append({
                'title': result.get('title', ''),
                'link': result.get('link', ''),
                'snippet': result.get('snippet', '')
            })
        
        return results


# Create default instance
default_client = SerpApi()

# Convenience functions using default client
def get_related_questions(keyword, location='Poland', lang='pl', limit=5):
    """Get related questions for a keyword using default client"""
    return default_client.get_related_questions(keyword, location, lang, limit)

def get_top_results(keyword, location='Poland', lang='pl', limit=5):
    """Get top search results for a keyword using default client"""
    return default_client.get_top_results(keyword, location, lang, limit)