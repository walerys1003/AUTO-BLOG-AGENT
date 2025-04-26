"""
SEO Analyzer

This module provides functions for analyzing SEO data and generating topics.
"""
import logging
import json
import time
from datetime import datetime
import random
from app import db
from models import ArticleTopic
from utils.seo.trends import get_daily_trends, get_related_topics
from utils.seo.serp import get_serp_data, analyze_serp_results
from utils.seo.topic_generator import generate_topics_from_trends

# Setup logging
logger = logging.getLogger(__name__)

def initialize_seo_module():
    """Initialize the SEO module"""
    logger.info("Initializing SEO module")
    
    # Test Google Trends API
    try:
        trends = get_daily_trends()
        logger.info(f"Google Trends API test successful. Found {len(trends)} trends")
    except Exception as e:
        logger.error(f"Google Trends API test failed: {str(e)}")
    
    # Initialize scheduler
    try:
        from utils.seo.scheduler import initialize_seo_scheduler
        initialize_seo_scheduler()
    except Exception as e:
        logger.error(f"Error initializing SEO scheduler: {str(e)}")
    
    logger.info("SEO module initialized successfully")
    return True

def run_seo_analysis(blog_id, categories=None):
    """
    Run SEO analysis for a blog and generate topics.
    
    Args:
        blog_id: The ID of the blog to analyze
        categories: List of categories to analyze
        
    Returns:
        List of generated topics
    """
    logger.info(f"Running SEO analysis for blog ID {blog_id}")
    
    # Get topics from Google Trends
    trends = []
    try:
        # Get daily trends
        daily_trends = get_daily_trends()
        if daily_trends:
            trends.extend(daily_trends)
            
        # Filter trends by categories if provided
        if categories:
            filtered_trends = []
            for trend in trends:
                # Check if trend matches any category
                if any(category.lower() in trend.lower() for category in categories):
                    filtered_trends.append(trend)
            
            # If we have at least 3 filtered trends, use those
            if len(filtered_trends) >= 3:
                trends = filtered_trends
    
    except Exception as e:
        logger.error(f"Error fetching trends: {str(e)}")
    
    # Generate topics from trends
    generated_topics = []
    try:
        if trends:
            topics = generate_topics_from_trends(trends, categories, blog_id)
            
            # Save topics to database
            for topic in topics:
                # Check if topic already exists
                existing = ArticleTopic.query.filter_by(
                    title=topic['title'],
                    blog_id=blog_id
                ).first()
                
                if not existing:
                    article_topic = ArticleTopic(
                        blog_id=blog_id,
                        title=topic['title'],
                        category=topic.get('category', ''),
                        status='pending',
                        score=topic.get('score', 0)
                    )
                    
                    # Set keywords
                    if 'keywords' in topic and topic['keywords']:
                        try:
                            article_topic.keywords = json.dumps(topic['keywords'])
                        except Exception as e:
                            logger.error(f"Error setting keywords: {str(e)}")
                    
                    db.session.add(article_topic)
                    generated_topics.append(topic)
            
            if generated_topics:
                db.session.commit()
                logger.info(f"Generated {len(generated_topics)} new topics for blog ID {blog_id}")
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error generating topics: {str(e)}")
    
    return generated_topics

def analyze_content(content, keywords=None):
    """
    Analyze content for SEO optimization.
    
    Args:
        content: The content to analyze
        keywords: List of target keywords
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Analyzing content for SEO optimization")
    
    results = {
        'word_count': len(content.split()),
        'readability': calculate_readability(content),
        'keyword_density': {},
        'recommendations': []
    }
    
    # Analyze keyword density
    if keywords:
        for keyword in keywords:
            count = content.lower().count(keyword.lower())
            density = (count / results['word_count']) * 100 if results['word_count'] > 0 else 0
            results['keyword_density'][keyword] = {
                'count': count,
                'density': round(density, 2)
            }
            
            # Add recommendations based on keyword density
            if density == 0:
                results['recommendations'].append(f"Keyword '{keyword}' not found in content. Consider adding it.")
            elif density < 0.5:
                results['recommendations'].append(f"Keyword '{keyword}' has low density ({density:.2f}%). Consider increasing it.")
            elif density > 3:
                results['recommendations'].append(f"Keyword '{keyword}' has high density ({density:.2f}%). Consider reducing it to avoid keyword stuffing.")
    
    # Check content length
    if results['word_count'] < 300:
        results['recommendations'].append("Content is too short. Consider adding more content (at least 300 words).")
    
    # Check readability
    if results['readability']['score'] > 50:
        results['recommendations'].append("Content readability is difficult. Consider simplifying language.")
    
    return results

def calculate_readability(text):
    """
    Calculate readability score for text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary containing readability metrics
    """
    # Split text into sentences and words
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    words = text.split()
    
    # Calculate metrics
    word_count = len(words)
    sentence_count = len(sentences)
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
    
    # Calculate syllable count (simplified approach)
    syllable_count = 0
    for word in words:
        word = word.lower()
        if len(word) <= 3:
            syllable_count += 1
        else:
            # Count vowel groups as syllables
            count = 0
            vowels = "aeiouy"
            if word[0] in vowels:
                count += 1
            for i in range(1, len(word)):
                if word[i] in vowels and word[i-1] not in vowels:
                    count += 1
            if word.endswith('e'):
                count -= 1
            if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
                count += 1
            if count == 0:
                count = 1
            syllable_count += count
    
    # Calculate average syllables per word
    avg_syllables_per_word = syllable_count / word_count if word_count > 0 else 0
    
    # Calculate Flesch-Kincaid Reading Ease
    if word_count > 0 and sentence_count > 0:
        flesch = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    else:
        flesch = 0
    
    # Clamp score between 0 and 100
    flesch = max(0, min(100, flesch))
    
    # Interpret score
    if flesch >= 90:
        difficulty = "Very Easy"
    elif flesch >= 80:
        difficulty = "Easy"
    elif flesch >= 70:
        difficulty = "Fairly Easy"
    elif flesch >= 60:
        difficulty = "Standard"
    elif flesch >= 50:
        difficulty = "Fairly Difficult"
    elif flesch >= 30:
        difficulty = "Difficult"
    else:
        difficulty = "Very Difficult"
    
    return {
        'score': 100 - flesch,  # Convert to difficulty score (0-100)
        'flesch_reading_ease': flesch,
        'difficulty': difficulty,
        'avg_sentence_length': avg_sentence_length,
        'avg_syllables_per_word': avg_syllables_per_word
    }