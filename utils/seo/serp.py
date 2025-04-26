"""
SERP API Interface

This module provides functions for interacting with SerpAPI data
"""
import logging
import json
import time
import requests
from config import Config

# Setup logging
logger = logging.getLogger(__name__)

def initialize_serp_client():
    """Initialize the SerpAPI client"""
    logger.info("SerpAPI client initialized")
    return True

def get_serp_data(query, country="pl", language="pl", page=1):
    """
    Get SERP data for a query using SerpAPI.
    
    Args:
        query: The search query
        country: The country code (default: 'pl')
        language: The language code (default: 'pl')
        page: The page number (default: 1)
        
    Returns:
        Dictionary containing SERP data
    """
    try:
        logger.info(f"Fetching SERP data for query: '{query}'")
        
        # Get API key from config
        api_key = Config.SERPAPI_KEY
        
        if not api_key:
            logger.error("SerpAPI key not found in configuration")
            return None
        
        # Base URL for the API
        base_url = "https://serpapi.com/search"
        
        # Parameters for the API request
        params = {
            'q': query,
            'gl': country,
            'hl': language,
            'page': page,
            'api_key': api_key
        }
        
        # Make the request
        response = requests.get(base_url, params=params)
        
        if response.status_code != 200:
            logger.error(f"SerpAPI request failed with status code: {response.status_code}")
            return None
        
        # Parse the response
        data = response.json()
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching SERP data: {str(e)}")
        return None

def analyze_serp_results(serp_data):
    """
    Analyze SERP results to extract useful information.
    
    Args:
        serp_data: The SERP data to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    if not serp_data:
        return None
    
    try:
        results = {
            'organic_results': [],
            'top_keywords': [],
            'avg_title_length': 0,
            'avg_snippet_length': 0,
            'recommendations': []
        }
        
        # Extract organic results
        if 'organic_results' in serp_data:
            organic_results = serp_data['organic_results']
            
            # Calculate average title and snippet length
            total_title_length = 0
            total_snippet_length = 0
            
            for result in organic_results:
                # Extract title and snippet
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                
                # Add to results
                results['organic_results'].append({
                    'position': result.get('position', 0),
                    'title': title,
                    'url': result.get('link', ''),
                    'snippet': snippet
                })
                
                # Update totals
                total_title_length += len(title.split())
                total_snippet_length += len(snippet.split())
            
            # Calculate averages
            num_results = len(organic_results)
            if num_results > 0:
                results['avg_title_length'] = total_title_length / num_results
                results['avg_snippet_length'] = total_snippet_length / num_results
        
        # Extract keywords from organic results
        keywords = {}
        
        for result in results['organic_results']:
            # Extract words from title
            title_words = result['title'].lower().split()
            
            for word in title_words:
                if len(word) > 3:  # Ignore short words
                    if word in keywords:
                        keywords[word] += 1
                    else:
                        keywords[word] = 1
        
        # Sort keywords by frequency
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        
        # Get top 10 keywords
        results['top_keywords'] = [keyword for keyword, _ in sorted_keywords[:10]]
        
        # Add recommendations
        if results['avg_title_length'] > 0:
            results['recommendations'].append(f"Average title length of top results: {results['avg_title_length']:.1f} words. Aim for similar length.")
        
        if results['avg_snippet_length'] > 0:
            results['recommendations'].append(f"Average meta description length of top results: {results['avg_snippet_length']:.1f} words. Aim for similar length.")
        
        if results['top_keywords']:
            results['recommendations'].append(f"Top keywords to target: {', '.join(results['top_keywords'][:5])}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing SERP results: {str(e)}")
        return None

def get_keyword_competition(keyword, country="pl", language="pl"):
    """
    Get keyword competition data using SerpAPI.
    
    Args:
        keyword: The keyword to analyze
        country: The country code (default: 'pl')
        language: The language code (default: 'pl')
        
    Returns:
        Dictionary containing competition data
    """
    try:
        logger.info(f"Analyzing competition for keyword: '{keyword}'")
        
        # Get SERP data for the keyword
        serp_data = get_serp_data(keyword, country, language)
        
        if not serp_data:
            return None
        
        # Analyze SERP results
        analysis = analyze_serp_results(serp_data)
        
        if not analysis:
            return None
        
        # Calculate competition metrics
        competition = {
            'keyword': keyword,
            'top_competitors': [],
            'difficulty': 0,
            'recommendations': []
        }
        
        # Extract top competitors
        if 'organic_results' in analysis:
            for result in analysis['organic_results'][:5]:  # Top 5 results
                domain = extract_domain(result['url'])
                competition['top_competitors'].append({
                    'domain': domain,
                    'title': result['title'],
                    'url': result['url']
                })
        
        # Calculate difficulty score based on top domains
        # This is a simplified approach - could be improved with domain authority data
        domain_weights = {
            'wikipedia.org': 95,
            'amazon.com': 90,
            'youtube.com': 85,
            'facebook.com': 80,
            'twitter.com': 75,
            'instagram.com': 75,
            'linkedin.com': 75,
            'gov.pl': 85,
            'edu.pl': 80
        }
        
        difficulty_score = 0
        for competitor in competition['top_competitors']:
            domain = competitor['domain']
            
            # Check if domain is a well-known site
            for known_domain, weight in domain_weights.items():
                if known_domain in domain:
                    difficulty_score += weight
                    break
            else:
                # Default weight for unknown domains
                difficulty_score += 50
        
        # Calculate average difficulty (0-100)
        num_competitors = len(competition['top_competitors'])
        if num_competitors > 0:
            competition['difficulty'] = min(100, difficulty_score / num_competitors)
        
        # Add recommendations based on difficulty
        if competition['difficulty'] > 80:
            competition['recommendations'].append(f"Very high competition. Consider targeting long-tail variations.")
        elif competition['difficulty'] > 60:
            competition['recommendations'].append(f"High competition. Focus on niche aspects or long-tail variations.")
        elif competition['difficulty'] > 40:
            competition['recommendations'].append(f"Medium competition. Create comprehensive content to compete.")
        else:
            competition['recommendations'].append(f"Lower competition. Create quality content targeting this keyword.")
        
        return competition
        
    except Exception as e:
        logger.error(f"Error analyzing keyword competition: {str(e)}")
        return None

def extract_domain(url):
    """Extract domain from URL"""
    try:
        # Remove protocol
        if '://' in url:
            domain = url.split('://')[1]
        else:
            domain = url
        
        # Remove path
        if '/' in domain:
            domain = domain.split('/')[0]
        
        return domain
        
    except Exception:
        return url