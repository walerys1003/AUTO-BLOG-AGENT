"""
Topic Generator

This module provides functions for generating article topics from trends and keywords.
"""
import logging
import random
import json
from models import ArticleTopic, db
from datetime import datetime
from .serp import get_serp_data, analyze_serp_results

# Setup logging
logger = logging.getLogger(__name__)

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
    
    if not trends:
        logger.warning("No trends provided for topic generation")
        return []
    
    topics = []
    for trend in trends[:limit * 2]:  # Process more trends than we need
        try:
            # Get SERP data for the trend
            serp_data = get_serp_data(trend)
            
            # Analyze SERP results
            serp_analysis = analyze_serp_results(serp_data)
            
            # Generate topic variations based on the trend and SERP analysis
            variations = generate_topic_variations(trend, serp_analysis, categories)
            
            # Take the first variation
            if variations:
                topic_data = variations[0]
                
                # Add blog ID if provided
                if blog_id:
                    # Create a new ArticleTopic object
                    topic = ArticleTopic(
                        title=topic_data['title'],
                        description=topic_data['description'],
                        keywords=json.dumps(topic_data['keywords']),
                        category=topic_data['category'],
                        blog_id=blog_id,
                        status='pending'
                    )
                    
                    # Add topic to the database
                    db.session.add(topic)
                    
                    # Generate additional topics if needed
                    if len(topics) >= limit:
                        break
                
                # Add topic to the list
                topics.append(topic_data)
                
                # Break if we have enough topics
                if len(topics) >= limit:
                    break
        
        except Exception as e:
            logger.error(f"Error generating topic for trend '{trend}': {str(e)}")
    
    # Commit changes to the database
    if blog_id:
        try:
            db.session.commit()
            logger.info(f"Generated {len(topics)} topics for blog ID {blog_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving topics to database: {str(e)}")
    
    return topics

def generate_topic_variations(trend, serp_analysis, categories=None):
    """
    Generate article topics in Polish based on a trend and SERP analysis.
    
    Args:
        trend: The trend term
        serp_analysis: SERP analysis data
        categories: List of categories to filter by
        
    Returns:
        List of generated topic variations in Polish
    """
    variations = []
    
    # Determine the best category for the topic
    best_category = get_best_category(trend, categories)
    current_year = datetime.now().year
    
    # Generate primary topic from the trend - in Polish
    primary_topic = {
        'title': f"{trend.capitalize()}: Kompletny Przewodnik",
        'description': f"Kompleksowy przewodnik na temat {trend.lower()}, zawierający wszystko, co musisz wiedzieć.",
        'keywords': [trend, f"{trend} poradnik", f"{trend} kompletny przewodnik", f"o {trend}"],
        'category': best_category
    }
    variations.append(primary_topic)
    
    # Generate "how to" variation - in Polish
    how_to_topic = {
        'title': f"Jak {trend.capitalize()} Krok po Kroku",
        'description': f"Dowiedz się, jak {trend.lower()} dzięki temu szczegółowemu poradnikowi krok po kroku.",
        'keywords': [trend, f"jak {trend}", f"{trend} kroki", f"{trend} poradnik"],
        'category': best_category
    }
    variations.append(how_to_topic)
    
    # Generate "X tips" variation - in Polish
    tips_count = random.choice([5, 7, 10, 12, 15])
    tips_topic = {
        'title': f"Top {tips_count} Porad dla {trend.capitalize()}",
        'description': f"Odkryj {tips_count} najlepszych porad dotyczących {trend.lower()}, które pomogą Ci osiągnąć sukces.",
        'keywords': [trend, f"{trend} porady", f"najlepsze {trend} wskazówki", f"{trend} poradnik"],
        'category': best_category
    }
    variations.append(tips_topic)
    
    # Generate "Ultimate guide" variation - in Polish
    ultimate_topic = {
        'title': f"Najpełniejszy Przewodnik po {trend.capitalize()} w {current_year} roku",
        'description': f"Najbardziej kompleksowy przewodnik po {trend.lower()} zaktualizowany na rok {current_year}.",
        'keywords': [trend, f"{trend} przewodnik", f"{trend} {current_year}", f"najlepszy {trend} poradnik"],
        'category': best_category
    }
    variations.append(ultimate_topic)
    
    # Add Polish-specific variations
    pl_specific_topic = {
        'title': f"{trend.capitalize()} - Wszystko Co Musisz Wiedzieć w {current_year}",
        'description': f"Praktyczny przewodnik na temat {trend.lower()} zawierający najnowsze informacje na rok {current_year}.",
        'keywords': [trend, f"{trend} praktyczne informacje", f"{trend} aktualności", f"wiedza o {trend}"],
        'category': best_category
    }
    variations.append(pl_specific_topic)
    
    return variations

def get_best_category(topic, available_categories=None):
    """
    Determine the best category for a topic.
    
    Args:
        topic: The topic to categorize
        available_categories: List of available categories
        
    Returns:
        Best matching category
    """
    # Default categories if none provided
    default_categories = [
        "Technology", "Business", "Health", "Entertainment", 
        "Travel", "Food", "Fashion", "Sports", "Education", "Lifestyle"
    ]
    
    categories = available_categories if available_categories else default_categories
    
    # Technology keywords
    tech_keywords = [
        "app", "software", "computer", "gadget", "tech", "digital", "mobile", 
        "phone", "laptop", "internet", "online", "device", "smart", "technology",
        "ai", "artificial intelligence", "machine learning", "code", "programming"
    ]
    
    # Business keywords
    business_keywords = [
        "business", "company", "startup", "entrepreneur", "invest", "market", 
        "finance", "money", "career", "job", "work", "professional", "industry",
        "economic", "economy", "corporate", "management", "strategy"
    ]
    
    # Health keywords
    health_keywords = [
        "health", "fitness", "exercise", "workout", "nutrition", "diet", "wellness", 
        "medical", "medicine", "doctor", "disease", "illness", "cure", "treatment",
        "healthy", "weight", "mental health", "therapy", "healing"
    ]
    
    # Entertainment keywords
    entertainment_keywords = [
        "movie", "film", "tv", "television", "show", "series", "actor", "actress", 
        "celebrity", "music", "song", "album", "artist", "concert", "festival",
        "entertainment", "game", "gaming", "video game", "book", "novel", "author"
    ]
    
    # Travel keywords
    travel_keywords = [
        "travel", "vacation", "trip", "tour", "destination", "hotel", "resort", 
        "flight", "airline", "beach", "mountain", "city", "country", "tourism",
        "adventure", "explore", "journey", "guide", "holiday"
    ]
    
    # Food keywords
    food_keywords = [
        "food", "recipe", "cook", "cooking", "meal", "dinner", "lunch", "breakfast", 
        "restaurant", "dish", "cuisine", "bake", "baking", "dessert", "snack",
        "drink", "beverage", "cocktail", "wine", "beer", "coffee", "tea"
    ]
    
    # All keywords
    all_keywords = {
        "Technology": tech_keywords,
        "Business": business_keywords,
        "Health": health_keywords,
        "Entertainment": entertainment_keywords,
        "Travel": travel_keywords,
        "Food": food_keywords,
    }
    
    # Count keyword matches for each category
    matches = {}
    for category, keywords in all_keywords.items():
        if category in categories:
            matches[category] = sum(1 for keyword in keywords if keyword.lower() in topic.lower())
    
    # Find the category with the most matches
    if matches:
        best_category = max(matches.items(), key=lambda x: x[1])[0]
        if matches[best_category] > 0:
            return best_category
    
    # Return a random category if no match found
    if categories:
        return random.choice(categories)
    else:
        return "Uncategorized"