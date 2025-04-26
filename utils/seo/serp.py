"""
SERP API Interface

This module provides functions for interacting with SerpAPI for SERP data.
"""
import logging
import os
import requests
import json
from urllib.parse import urlparse

# Setup logging
logger = logging.getLogger(__name__)

# Get SerpAPI key from environment
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "57d393880136bab7d3159bf1d56d251fa3945bf56e6d1fa3448199e7c10e069c")

def initialize_serp_client():
    """Initialize the SerpAPI client"""
    logger.info("Initializing SerpAPI client")
    if not SERPAPI_KEY:
        logger.warning("SERPAPI_KEY not found in environment variables")
        return False
    else:
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
    logger.info(f"Getting SERP data for query: {query}")
    
    if not SERPAPI_KEY:
        logger.error("SERPAPI_KEY not found in environment variables")
        return {}
    
    # Construct API URL
    base_url = "https://serpapi.com/search"
    
    # Set parameters
    params = {
        "api_key": SERPAPI_KEY,
        "q": query,
        "gl": country,
        "hl": language,
        "start": (page - 1) * 10,
        "google_domain": f"google.{country}"
    }
    
    try:
        # Make API request
        response = requests.get(base_url, params=params)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Extract useful information
            serp_data = {
                "query": query,
                "organic_results": [],
                "related_searches": [],
                "knowledge_graph": {},
                "top_stories": []
            }
            
            # Extract organic results
            if "organic_results" in data:
                for result in data["organic_results"]:
                    serp_data["organic_results"].append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("snippet", ""),
                        "domain": extract_domain(result.get("link", "")),
                        "position": result.get("position", 0)
                    })
            
            # Extract related searches
            if "related_searches" in data:
                for search in data["related_searches"]:
                    serp_data["related_searches"].append(search.get("query", ""))
            
            # Extract knowledge graph
            if "knowledge_graph" in data:
                kg = data["knowledge_graph"]
                serp_data["knowledge_graph"] = {
                    "title": kg.get("title", ""),
                    "description": kg.get("description", ""),
                    "type": kg.get("type", "")
                }
            
            # Extract top stories
            if "top_stories" in data:
                for story in data["top_stories"]:
                    serp_data["top_stories"].append({
                        "title": story.get("title", ""),
                        "link": story.get("link", ""),
                        "source": story.get("source", ""),
                        "published_date": story.get("date", "")
                    })
            
            return serp_data
        else:
            logger.error(f"SerpAPI request failed with status code: {response.status_code}")
            return {}
    
    except Exception as e:
        logger.error(f"Error getting SERP data: {str(e)}")
        return {}

def analyze_serp_results(serp_data):
    """
    Analyze SERP results to extract useful information.
    
    Args:
        serp_data: The SERP data to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info("Analyzing SERP results")
    
    analysis = {
        "top_domains": [],
        "common_words_in_titles": {},
        "avg_title_length": 0,
        "avg_snippet_length": 0,
        "has_knowledge_graph": False,
        "has_top_stories": False
    }
    
    if not serp_data or "organic_results" not in serp_data or not serp_data["organic_results"]:
        logger.warning("No SERP data to analyze")
        return analysis
    
    # Extract domains
    domains = [result["domain"] for result in serp_data["organic_results"] if "domain" in result]
    domain_counts = {}
    for domain in domains:
        if domain in domain_counts:
            domain_counts[domain] += 1
        else:
            domain_counts[domain] = 1
    
    # Sort domains by count
    sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
    analysis["top_domains"] = [{"domain": domain, "count": count} for domain, count in sorted_domains[:5]]
    
    # Analyze titles
    titles = [result["title"] for result in serp_data["organic_results"] if "title" in result]
    title_length_sum = sum(len(title) for title in titles)
    analysis["avg_title_length"] = title_length_sum / len(titles) if titles else 0
    
    # Analyze snippets
    snippets = [result["snippet"] for result in serp_data["organic_results"] if "snippet" in result]
    snippet_length_sum = sum(len(snippet) for snippet in snippets)
    analysis["avg_snippet_length"] = snippet_length_sum / len(snippets) if snippets else 0
    
    # Check for knowledge graph
    analysis["has_knowledge_graph"] = bool(serp_data.get("knowledge_graph", {}))
    
    # Check for top stories
    analysis["has_top_stories"] = bool(serp_data.get("top_stories", []))
    
    return analysis

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
    logger.info(f"Getting keyword competition for: {keyword}")
    
    # Get SERP data
    serp_data = get_serp_data(keyword, country, language)
    
    # Prepare competition data
    competition = {
        "keyword": keyword,
        "difficulty": "unknown",
        "difficulty_score": 0,
        "top_competitors": [],
        "recommended_content_length": 0,
        "recommended_headings": 0,
        "suggested_keywords": serp_data.get("related_searches", [])
    }
    
    # If no SERP data, return default competition data
    if not serp_data or "organic_results" not in serp_data or not serp_data["organic_results"]:
        logger.warning(f"No SERP data found for keyword: {keyword}")
        competition["difficulty"] = "unknown"
        return competition
    
    # Calculate difficulty based on domain authority
    organic_results = serp_data["organic_results"]
    top_domains = [result["domain"] for result in organic_results[:5] if "domain" in result]
    
    # Check for known high authority domains
    high_authority_domains = ["wikipedia.org", "amazon.com", "youtube.com", "facebook.com", 
                             "twitter.com", "linkedin.com", "instagram.com", "pinterest.com",
                             "reddit.com", "quora.com", "nytimes.com", "bbc.com", "cnn.com",
                             "github.com", "medium.com", "forbes.com", "wsj.com", "bloomberg.com"]
    
    # Count high authority domains in top results
    high_authority_count = sum(1 for domain in top_domains if any(auth_domain in domain for auth_domain in high_authority_domains))
    
    # Calculate difficulty score (0-100)
    difficulty_score = min(100, (high_authority_count / len(top_domains) * 100) + (len(organic_results) / 10 * 20))
    competition["difficulty_score"] = round(difficulty_score, 1)
    
    # Determine difficulty level
    if difficulty_score < 30:
        competition["difficulty"] = "easy"
        competition["recommended_content_length"] = 800
        competition["recommended_headings"] = 3
    elif difficulty_score < 60:
        competition["difficulty"] = "moderate"
        competition["recommended_content_length"] = 1200
        competition["recommended_headings"] = 5
    else:
        competition["difficulty"] = "hard"
        competition["recommended_content_length"] = 2000
        competition["recommended_headings"] = 7
    
    # Get top competitors
    for result in organic_results[:5]:
        if "domain" in result and "title" in result:
            competition["top_competitors"].append({
                "domain": result["domain"],
                "title": result["title"],
                "url": result.get("link", "")
            })
    
    return competition

def extract_domain(url):
    """Extract domain from URL"""
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Remove www. if present
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain
    except Exception:
        return ""