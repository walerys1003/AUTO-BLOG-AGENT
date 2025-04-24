import logging
import json
import random
from typing import List, Dict, Any, Optional
from config import Config
import traceback
from utils.helpers import get_ai_response

# Setup logging
logger = logging.getLogger(__name__)

def generate_article_topics(
    blog_name: str,
    categories: Optional[List[str]] = None,
    count: int = 5,
    custom_prompt: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate SEO-optimized article topics based on blog name and categories
    
    Args:
        blog_name: Name of the blog
        categories: List of blog categories to focus on
        count: Number of topics to generate
        custom_prompt: Optional custom prompt to override the default
        
    Returns:
        List of topic dictionaries with title, keywords, and category
    """
    try:
        # Use default categories if none provided
        if not categories or len(categories) == 0:
            categories = ["General", "News", "Guides"]
        
        # Create system prompt for topic generation
        system_prompt = f"""You are an SEO expert and content strategist helping to generate article ideas for a blog called '{blog_name}'.
Your task is to create {count} engaging, highly-searchable article topics that will rank well in search engines and attract readers.
"""

        # Construct the main user prompt
        if custom_prompt:
            user_prompt = custom_prompt
        else:
            user_prompt = f"""Generate {count} SEO-optimized article topics for a blog named '{blog_name}'.

The blog covers these categories: {', '.join(categories)}

For each topic, provide:
1. An engaging title that includes SEO keywords (60-80 characters)
2. A list of 5-8 target keywords (including long-tail keywords)
3. The most appropriate category from the list above
4. An SEO score from 0.1 to 1.0 representing the potential search traffic (higher is better)

Format your response as a valid JSON array with objects containing these fields:
- title (string): The article title with proper capitalization
- keywords (array): List of keywords as strings 
- category (string): One of the categories listed above
- score (number): SEO potential score between 0.1 and 1.0

Make sure all titles are unique, engaging, specific, and clearly communicate value to the reader.
Focus on topics that people are actively searching for, including "how to" guides, listicles, and problem-solving content.
"""

        # Set up JSON response format
        response_format = {"type": "json_object"}
        
        # Get response from AI
        response = get_ai_response(
            prompt=user_prompt,
            model=Config.DEFAULT_TOPIC_MODEL,
            temperature=0.7,
            response_format=response_format,
            system_prompt=system_prompt
        )
        
        # Process response
        if isinstance(response, dict) and 'topics' in response:
            # If response came as a wrapper object with a 'topics' key
            topics = response['topics']
        elif isinstance(response, list):
            # If response came directly as a list
            topics = response
        else:
            # Try to parse if we got a string but expected JSON
            if isinstance(response, str):
                try:
                    parsed = json.loads(response)
                    if isinstance(parsed, dict) and 'topics' in parsed:
                        topics = parsed['topics']
                    elif isinstance(parsed, list):
                        topics = parsed
                    else:
                        logger.error(f"Unexpected response format: {parsed}")
                        return []
                except:
                    logger.error(f"Failed to parse response as JSON: {response}")
                    return []
            else:
                logger.error(f"Unexpected response type: {type(response)}")
                return []
        
        # Validate and clean up topics
        valid_topics = []
        for topic in topics:
            if isinstance(topic, dict) and 'title' in topic and 'keywords' in topic:
                # Ensure we have all required fields with proper types
                valid_topic = {
                    'title': str(topic.get('title', '')).strip(),
                    'keywords': [str(k).strip() for k in topic.get('keywords', []) if k],
                    'category': str(topic.get('category', categories[0])).strip(),
                    'score': float(topic.get('score', 0.5))
                }
                
                # Add to valid topics if title is not empty
                if valid_topic['title']:
                    valid_topics.append(valid_topic)
        
        # If we have fewer topics than requested, log warning
        if len(valid_topics) < count:
            logger.warning(f"Generated only {len(valid_topics)} valid topics out of {count} requested")
        
        # Return topics, limiting to requested count
        return valid_topics[:count]
        
    except Exception as e:
        logger.error(f"Error generating article topics: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def analyze_topic_competition(topic: str, keywords: List[str]) -> Dict[str, Any]:
    """
    Analyze competition level for a topic and its keywords
    
    Args:
        topic: The article topic/title
        keywords: List of keywords for the topic
        
    Returns:
        Dictionary with competition analysis
    """
    try:
        # This would normally call an SEO API or web scraping service
        # For now, return a simulated analysis
        
        # Simulate competition levels for keywords
        keyword_analysis = []
        for keyword in keywords:
            # Generate random metrics for demo
            volume = random.randint(500, 15000)
            difficulty = random.uniform(0.1, 0.9)
            competition = "High" if difficulty > 0.7 else "Medium" if difficulty > 0.4 else "Low"
            
            keyword_analysis.append({
                "keyword": keyword,
                "volume": volume,
                "difficulty": round(difficulty, 2),
                "competition": competition
            })
        
        # Sort by volume (highest first)
        keyword_analysis.sort(key=lambda x: x["volume"], reverse=True)
        
        # Overall score - average of difficulty scores, inverted (lower difficulty = higher score)
        avg_difficulty = sum(k["difficulty"] for k in keyword_analysis) / len(keyword_analysis)
        potential_score = round(1 - avg_difficulty, 2)
        
        return {
            "topic": topic,
            "overall_score": potential_score,
            "keyword_analysis": keyword_analysis,
            "recommendation": "Proceed" if potential_score > 0.4 else "Consider alternatives"
        }
            
    except Exception as e:
        logger.error(f"Error analyzing topic competition: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return basic analysis on error
        return {
            "topic": topic,
            "overall_score": 0.5,
            "keyword_analysis": [{"keyword": k, "volume": 1000, "difficulty": 0.5, "competition": "Medium"} for k in keywords],
            "recommendation": "Error in analysis, proceed with caution"
        }