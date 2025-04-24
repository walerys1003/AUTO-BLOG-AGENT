import requests
import logging
import json
import random
from typing import List, Dict, Any, Tuple
import traceback
from bs4 import BeautifulSoup
from config import Config
from utils.helpers import get_ai_response

# Setup logging
logger = logging.getLogger(__name__)

def get_trending_keywords(category: str, country_code: str = "US") -> List[str]:
    """
    Fetch trending keywords for a specific category using Google Trends or similar APIs.
    Falls back to a generic approach if API is unavailable.
    
    Args:
        category: The category to get trending keywords for
        country_code: The country code to get trends for (default: US)
        
    Returns:
        List of trending keywords
    """
    try:
        # This is a simplified approach. In a production environment,
        # you would use a proper Google Trends API or similar service.
        # For demonstration, we'll make a simplified request to get trending topics.
        
        # Basic scraping of Google Trends - note this is not reliable for production
        # and should be replaced with a proper API
        url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={country_code}"
        response = requests.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "xml")
            items = soup.find_all("item")
            keywords = []
            
            for item in items:
                title = item.find("title").text
                # If category filter is provided, apply it (simplified)
                if not category or category.lower() in title.lower():
                    keywords.append(title)
            
            return keywords[:10]  # Return top 10 trending keywords
        else:
            logger.warning(f"Failed to fetch trending keywords: {response.status_code}")
            # Fall back to AI-generated relevant keywords
            return generate_keywords_with_ai(category)
            
    except Exception as e:
        logger.error(f"Error fetching trending keywords: {str(e)}")
        logger.error(traceback.format_exc())
        # Fall back to AI-generated relevant keywords
        return generate_keywords_with_ai(category)

def generate_keywords_with_ai(category: str) -> List[str]:
    """
    Generate relevant keywords for a category using AI when API calls fail
    
    Args:
        category: The category to generate keywords for
        
    Returns:
        List of generated keywords
    """
    prompt = f"""
    Generate a list of 10 trending and relevant keywords or phrases for the category: {category}.
    These should be popular search terms that people might use when looking for content in this category.
    Format the response as a JSON array of strings.
    """
    
    try:
        response = get_ai_response(
            prompt=prompt,
            model=Config.DEFAULT_TOPIC_MODEL,
            response_format={"type": "json_object"}
        )
        
        if response and isinstance(response, dict) and "keywords" in response:
            return response["keywords"]
        elif response and isinstance(response, list):
            return response
        else:
            logger.warning("AI response format unexpected, using fallback keywords")
            return fallback_keywords_by_category(category)
    
    except Exception as e:
        logger.error(f"Error generating keywords with AI: {str(e)}")
        return fallback_keywords_by_category(category)

def fallback_keywords_by_category(category: str) -> List[str]:
    """
    Provide fallback keywords when all other methods fail
    
    Args:
        category: The category to get fallback keywords for
        
    Returns:
        List of fallback keywords
    """
    # Dictionary of fallback keywords by common categories
    fallbacks = {
        "technology": ["latest tech trends", "ai development", "smartphone review", 
                      "future technology", "tech innovation", "coding tutorial",
                      "software development", "cybersecurity tips", "web development",
                      "tech gadgets 2023"],
        "health": ["healthy lifestyle", "fitness tips", "mental health", 
                  "nutrition guide", "workout routine", "wellness practices",
                  "diet plans", "medical breakthroughs", "health supplements",
                  "preventive healthcare"],
        "finance": ["investment strategies", "personal finance", "stock market tips", 
                   "cryptocurrency trends", "retirement planning", "budget tips",
                   "financial freedom", "wealth building", "saving strategies",
                   "tax optimization"],
        "travel": ["travel destinations", "vacation tips", "budget travel", 
                  "adventure tourism", "travel hacks", "hidden gems",
                  "luxury resorts", "backpacking guide", "family vacation",
                  "travel photography"],
        "food": ["easy recipes", "cooking tips", "healthy meals", 
                "food trends", "baking guide", "restaurant reviews",
                "international cuisine", "vegetarian recipes", "meal prep",
                "cooking techniques"]
    }
    
    # Find the closest category or use general keywords
    for key in fallbacks:
        if key in category.lower():
            return fallbacks[key]
    
    # General keywords if no category match
    return [
        "how to guide", "tips and tricks", "beginners guide",
        "expert advice", "step by step tutorial", "comprehensive review",
        "ultimate guide", "essential tips", "best practices",
        "complete walkthrough"
    ]

def generate_article_topics(category: str, blog_name: str, count: int = 4) -> List[Dict[str, Any]]:
    """
    Generate article topics based on trending keywords and SEO analysis
    
    Args:
        category: The category to generate topics for
        blog_name: The name of the blog for context
        count: Number of topics to generate
        
    Returns:
        List of article topic dictionaries with title, keywords, and score
    """
    try:
        # Get trending keywords for the category
        keywords = get_trending_keywords(category)
        
        if not keywords:
            logger.warning(f"No keywords found for category {category}, using fallbacks")
            keywords = fallback_keywords_by_category(category)
        
        # Use AI to generate article topics based on keywords
        prompt = f"""
        Generate {count} compelling and SEO-optimized article ideas for a blog named "{blog_name}" 
        in the category "{category}".
        
        Use these trending keywords as inspiration: {', '.join(keywords)}
        
        For each article idea, provide:
        1. An engaging title (60-70 characters, include a primary keyword naturally)
        2. A list of 5-7 relevant keywords/phrases for the article
        3. An SEO score (1-100) based on potential search interest
        
        Format your response as a JSON array of objects with "title", "keywords", and "score" fields.
        """
        
        response = get_ai_response(
            prompt=prompt,
            model=Config.DEFAULT_TOPIC_MODEL,
            response_format={"type": "json_object"}
        )
        
        if response and isinstance(response, dict) and "topics" in response:
            return response["topics"]
        elif response and isinstance(response, list):
            return response
        else:
            logger.warning("Invalid response format from AI, generating basic topics")
            return generate_basic_topics(category, blog_name, keywords, count)
            
    except Exception as e:
        logger.error(f"Error generating article topics: {str(e)}")
        logger.error(traceback.format_exc())
        # Fall back to basic topic generation
        return generate_basic_topics(category, blog_name, fallback_keywords_by_category(category), count)

def generate_basic_topics(category: str, blog_name: str, keywords: List[str], count: int) -> List[Dict[str, Any]]:
    """
    Generate basic article topics when AI generation fails
    
    Args:
        category: The category for topics
        blog_name: The blog name
        keywords: List of keywords to use
        count: Number of topics to generate
        
    Returns:
        List of basic article topics
    """
    topics = []
    
    # Template formats for article titles
    templates = [
        "The Ultimate Guide to {keyword}",
        "10 Essential Tips for {keyword} in 2023",
        "How to Master {keyword}: A Beginner's Guide",
        "Why {keyword} Matters: Expert Insights",
        "{keyword}: What You Need to Know",
        "The Future of {keyword}: Trends and Predictions",
        "Understanding {keyword}: A Comprehensive Guide",
        "{keyword} 101: Everything You Need to Know",
        "The Pros and Cons of {keyword}",
        "Mastering {keyword}: Advanced Techniques"
    ]
    
    # Generate topics based on templates and keywords
    for i in range(min(count, len(keywords))):
        keyword = keywords[i]
        template = random.choice(templates)
        title = template.format(keyword=keyword)
        
        # Generate some related keywords
        related_keywords = [k for k in keywords if k != keyword][:5]
        if len(related_keywords) < 5:
            related_keywords.extend([f"{keyword} tips", f"{keyword} guide", f"best {keyword}", f"{keyword} techniques"])
        
        topics.append({
            "title": title,
            "keywords": [keyword] + related_keywords[:6],
            "score": random.randint(70, 95)  # Assign a random high score
        })
    
    return topics[:count]
